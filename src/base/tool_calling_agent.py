# coding=utf-8

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import importlib
import inspect
import json
import os
import re
import tempfile
import textwrap
import time
from abc import ABC, abstractmethod
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional, Set, Tuple, TypedDict, Union

import jinja2
import yaml
from huggingface_hub import create_repo, metadata_update, snapshot_download, upload_folder
from jinja2 import StrictUndefined, Template
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich import box


if TYPE_CHECKING:
    import PIL.Image

from src.memory import (ActionStep,
                        ToolCall)
from src.models import (
    ChatMessage,
)
from src.logger import (
    LogLevel,
)

from src.tools import Tool
from src.exception import (
    AgentParsingError,
    AgentToolCallError,
    AgentToolExecutionError,
    AgentGenerationError,
)
from src.base.multistep_agent import MultiStepAgent, PromptTemplates, populate_template
from src.models import Model
from src.models.base import parse_json_if_needed
from src.utils.agent_types import AgentImage, AgentAudio

from src.logger import logger, YELLOW_HEX
from src.monitoring import monitor, broadcast_thinking, broadcast_decision

class ToolCallingAgent(MultiStepAgent):
    """
    This agent uses JSON-like tool calls, using method `model.get_tool_call` to leverage the LLM engine's tool calling capabilities.

    Args:
        tools (`list[Tool]`): [`Tool`]s that the agent can use.
        model (`Callable[[list[dict[str, str]]], ChatMessage]`): Model that will generate the agent's actions.
        prompt_templates ([`~agents.PromptTemplates`], *optional*): Prompt templates.
        planning_interval (`int`, *optional*): Interval at which the agent will run a planning step.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        tools: list[Tool],
        model: Model,
        prompt_templates: PromptTemplates | None = None,
        planning_interval: int | None = None,
        **kwargs,
    ):
        prompt_templates = prompt_templates or yaml.safe_load(
            importlib.resources.files("src.base.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        super().__init__(
            tools=tools,
            model=model,
            prompt_templates=prompt_templates,
            planning_interval=planning_interval,
            **kwargs,
        )

    def initialize_system_prompt(self) -> str:
        system_prompt = populate_template(
            self.prompt_templates["system_prompt"],
            variables={"tools": self.tools, "managed_agents": self.managed_agents},
        )
        return system_prompt

    def step(self, memory_step: ActionStep) -> None | Any:
        """
        Perform one step in the ReAct framework: the agent thinks, acts, and observes the result.
        Returns None if the step is not final.
        """
        import asyncio
        
        # Model çağrısı başlangıcı
        asyncio.create_task(monitor.broadcast_step(
            "model_thinking",
            f"🧠 Model Düşünüyor",
            f"Adım {self.step_number} için model çağrısı yapılıyor",
            {"step_number": getattr(self, 'step_number', 0)},
            getattr(self, 'name', 'agent')
        ))
        
        memory_messages = self.write_memory_to_messages()

        input_messages = memory_messages.copy()

        # Add new step in logs
        memory_step.model_input_messages = input_messages

        try:
            # Model input detayları
            asyncio.create_task(monitor.broadcast_step(
                "model_input",
                f"📝 Model Girdisi Hazırlandı",
                f"Mesaj sayısı: {len(input_messages)}, Tool sayısı: {len(self.tools)}",
                {"message_count": len(input_messages), "tool_count": len(self.tools)},
                getattr(self, 'name', 'agent')
            ))
            
            chat_message: ChatMessage = self.model(
                input_messages,
                stop_sequences=["Observation:", "Calling tools:"],
                tools_to_call_from=list(self.tools.values()),
            )
            memory_step.model_output_message = chat_message
            model_output = chat_message.content
            
            # Model çıktısı alındı
            asyncio.create_task(monitor.broadcast_step(
                "model_output",
                f"🤖 Model Cevabı Alındı",
                f"Çıktı uzunluğu: {len(model_output) if model_output else 0} karakter",
                {"output_length": len(model_output) if model_output else 0},
                getattr(self, 'name', 'agent')
            ))
            
            self.logger.log_markdown(
                content=model_output if model_output else str(chat_message.raw),
                title="Output message of the LLM:",
                level=LogLevel.DEBUG,
            )

            memory_step.model_output_message.content = model_output
            memory_step.model_output = model_output
        except Exception as e:
            # Model hatası
            asyncio.create_task(monitor.broadcast_step(
                "model_error",
                f"❌ Model Hatası",
                f"Model çağrısında hata: {str(e)}",
                {"error": str(e)},
                getattr(self, 'name', 'agent')
            ))
            raise AgentGenerationError(f"Error while generating output:\n{e}", self.logger) from e

        # Tool call parsing başlangıcı
        asyncio.create_task(monitor.broadcast_step(
            "tool_parsing",
            f"🔍 Tool Çağrısı Ayrıştırılıyor",
            f"Model çıktısından tool çağrısı bulunuyor",
            {},
            getattr(self, 'name', 'agent')
        ))

        if chat_message.tool_calls is None or len(chat_message.tool_calls) == 0:
            try:
                chat_message = self.model.parse_tool_calls(chat_message)
            except Exception as e:
                asyncio.create_task(monitor.broadcast_step(
                    "parsing_error",
                    f"❌ Ayrıştırma Hatası",
                    f"Tool çağrısı ayrıştırılamadı: {str(e)}",
                    {"error": str(e)},
                    getattr(self, 'name', 'agent')
                ))
                raise AgentParsingError(f"Error while parsing tool call from model output: {e}", self.logger)
        else:
            for tool_call in chat_message.tool_calls:
                tool_call.function.arguments = parse_json_if_needed(tool_call.function.arguments)
                
        tool_call = chat_message.tool_calls[0]  # type: ignore
        tool_name, tool_call_id = tool_call.function.name, tool_call.id
        tool_arguments = tool_call.function.arguments
        memory_step.model_output = str(f"Called Tool: '{tool_name}' with arguments: {tool_arguments}")
        memory_step.tool_calls = [ToolCall(name=tool_name, arguments=tool_arguments, id=tool_call_id)]

        # Tool çağrısı bulundu
        asyncio.create_task(monitor.broadcast_step(
            "tool_found",
            f"🔧 Tool Çağrısı Bulundu",
            f"Tool: {tool_name}, Parametreler: {str(tool_arguments)[:100]}...",
            {"tool_name": tool_name, "arguments": str(tool_arguments)[:200]},
            getattr(self, 'name', 'agent')
        ))

        # Execute
        self.logger.log(
            Panel(Text(f"Calling tool: '{tool_name}' with arguments: {tool_arguments}")),
            level=LogLevel.INFO,
        )
        if tool_name == "final_answer":
            # Final answer işlemi
            asyncio.create_task(monitor.broadcast_step(
                "final_answer_processing",
                f"🎯 Final Cevap İşleniyor",
                f"Final answer hazırlanıyor",
                {"tool_name": tool_name},
                getattr(self, 'name', 'agent')
            ))
            
            if isinstance(tool_arguments, dict):
                if "answer" in tool_arguments:
                    answer = tool_arguments["answer"]
                else:
                    answer = tool_arguments
            else:
                answer = tool_arguments
            if (
                isinstance(answer, str) and answer in self.state.keys()
            ):  # if the answer is a state variable, return the value
                final_answer = self.state[answer]
                self.logger.log(
                    f"[bold {YELLOW_HEX}]Final answer:[/bold {YELLOW_HEX}] Extracting key '{answer}' from state to return value '{final_answer}'.",
                    level=LogLevel.INFO,
                )
            else:
                final_answer = answer
                self.logger.log(
                    Text(f"Final answer: {final_answer}", style=f"bold {YELLOW_HEX}"),
                    level=LogLevel.INFO,
                )

            memory_step.action_output = final_answer
            return final_answer
        else:
            # Regular tool execution
            asyncio.create_task(monitor.broadcast_step(
                "tool_execution_start",
                f"⚡ Tool Çalıştırılıyor",
                f"'{tool_name}' tool'u çalıştırılmaya başlandı",
                {"tool_name": tool_name, "arguments": str(tool_arguments)[:200]},
                getattr(self, 'name', 'agent')
            ))
            
            if tool_arguments is None:
                tool_arguments = {}
            observation = self.execute_tool_call(tool_name, tool_arguments)
            
            # Tool execution tamamlandı
            observation_type = type(observation)
            if observation_type in [AgentImage, AgentAudio]:
                if observation_type == AgentImage:
                    observation_name = "image.png"
                elif observation_type == AgentAudio:
                    observation_name = "audio.mp3"
                # TODO: observation naming could allow for different names of same type

                self.state[observation_name] = observation
                updated_information = f"Stored '{observation_name}' in memory."
            else:
                updated_information = str(observation).strip()
                
            # Tool sonucu alındı
            asyncio.create_task(monitor.broadcast_step(
                "tool_result",
                f"✅ Tool Sonucu Alındı",
                f"'{tool_name}' tool'u tamamlandı: {updated_information[:100]}...",
                {"tool_name": tool_name, "result": updated_information[:300]},
                getattr(self, 'name', 'agent')
            ))
            
            self.logger.log(
                f"Observations: {updated_information.replace('[', '|')}",  # escape potential rich-tag-like components
                level=LogLevel.INFO,
            )
            memory_step.observations = updated_information
            return None

    def _substitute_state_variables(self, arguments: dict[str, str] | str) -> dict[str, Any] | str:
        """Replace string values in arguments with their corresponding state values if they exist."""
        if isinstance(arguments, dict):
            return {
                key: self.state.get(value, value) if isinstance(value, str) else value
                for key, value in arguments.items()
            }
        return arguments

    def execute_tool_call(self, tool_name: str, arguments: dict[str, str] | str) -> Any:
        """
        Execute a tool or managed agent with the provided arguments.

        The arguments are replaced with the actual values from the state if they refer to state variables.

        Args:
            tool_name (`str`): Name of the tool or managed agent to execute.
            arguments (dict[str, str] | str): Arguments passed to the tool call.
        """
        import asyncio
        
        # Tool çalıştırma başlangıcı
        asyncio.create_task(monitor.broadcast_step(
            "tool_execution_detail",
            f"🔧 '{tool_name}' Hazırlanıyor",
            f"Tool parametreleri kontrol ediliyor",
            {"tool_name": tool_name, "arguments": str(arguments)[:200]},
            getattr(self, 'name', 'agent')
        ))
        
        # Check if the tool exists
        available_tools = {**self.tools, **self.managed_agents}
        if tool_name not in available_tools:
            asyncio.create_task(monitor.broadcast_step(
                "tool_not_found",
                f"❌ Tool Bulunamadı",
                f"'{tool_name}' tool'u mevcut değil. Mevcut tool'lar: {', '.join(list(available_tools.keys())[:3])}...",
                {"tool_name": tool_name, "available_tools": list(available_tools.keys())[:5]},
                getattr(self, 'name', 'agent')
            ))
            raise AgentToolExecutionError(
                f"Unknown tool {tool_name}, should be one of: {', '.join(available_tools)}.", self.logger
            )

        # Get the tool and substitute state variables in arguments
        tool = available_tools[tool_name]
        arguments = self._substitute_state_variables(arguments)
        is_managed_agent = tool_name in self.managed_agents
        
        # Tool tipi ve parametreler
        tool_type = "Yönetilen Agent" if is_managed_agent else "Tool"
        asyncio.create_task(monitor.broadcast_step(
            "tool_prepare",
            f"⚙️ {tool_type} Çalıştırılıyor",
            f"'{tool_name}' {tool_type.lower()}'ı parametrelerle birlikte çalıştırılıyor",
            {"tool_name": tool_name, "tool_type": tool_type, "is_managed_agent": is_managed_agent},
            getattr(self, 'name', 'agent')
        ))

        try:
            # Call tool with appropriate arguments
            if isinstance(arguments, dict):
                result = tool(**arguments) if is_managed_agent else tool(**arguments, sanitize_inputs_outputs=True)
            elif isinstance(arguments, str):
                result = tool(arguments) if is_managed_agent else tool(arguments, sanitize_inputs_outputs=True)
            else:
                raise TypeError(f"Unsupported arguments type: {type(arguments)}")
            
            # Tool başarıyla tamamlandı
            result_preview = str(result)[:200] if result else "Sonuç alındı"
            asyncio.create_task(monitor.broadcast_step(
                "tool_success",
                f"✅ '{tool_name}' Başarılı",
                f"Tool başarıyla tamamlandı: {result_preview}...",
                {"tool_name": tool_name, "result_length": len(str(result)), "result_preview": result_preview},
                getattr(self, 'name', 'agent')
            ))
            
            return result

        except TypeError as e:
            # Handle invalid arguments
            description = getattr(tool, "description", "No description")
            if is_managed_agent:
                error_msg = (
                    f"Invalid request to team member '{tool_name}' with arguments {json.dumps(arguments, ensure_ascii=False)}: {e}\n"
                    "You should call this team member with a valid request.\n"
                    f"Team member description: {description}"
                )
            else:
                error_msg = (
                    f"Invalid call to tool '{tool_name}' with arguments {json.dumps(arguments, ensure_ascii=False)}: {e}\n"
                    "You should call this tool with correct input arguments.\n"
                    f"Expected inputs: {json.dumps(tool.parameters)}\n"
                    f"Returns output type: {tool.output_type}\n"
                    f"Tool description: '{description}'"
                )
            
            # Tool parametresi hatası
            asyncio.create_task(monitor.broadcast_step(
                "tool_parameter_error",
                f"❌ '{tool_name}' Parametre Hatası",
                f"Geçersiz parametreler: {str(e)}",
                {"tool_name": tool_name, "error": str(e), "error_type": "TypeError"},
                getattr(self, 'name', 'agent')
            ))
            
            raise AgentToolCallError(error_msg, self.logger) from e

        except Exception as e:
            # Handle execution errors
            if is_managed_agent:
                error_msg = (
                    f"Error executing request to team member '{tool_name}' with arguments {json.dumps(arguments)}: {e}\n"
                    "Please try again or request to another team member"
                )
            else:
                error_msg = (
                    f"Error executing tool '{tool_name}' with arguments {json.dumps(arguments)}: {type(e).__name__}: {e}\n"
                    "Please try again or use another tool"
                )
            
            # Tool execution hatası
            asyncio.create_task(monitor.broadcast_step(
                "tool_execution_error",
                f"❌ '{tool_name}' Çalışma Hatası",
                f"Tool çalıştırma hatası: {str(e)}",
                {"tool_name": tool_name, "error": str(e), "error_type": type(e).__name__},
                getattr(self, 'name', 'agent')
            ))
            
            raise AgentToolExecutionError(error_msg, self.logger) from e