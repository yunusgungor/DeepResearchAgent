/*
DeepResearchAgent React Web UI
Modern React tabanlı kullanıcı arayüzü
*/

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Layout, Menu, Button, Input, Card, Tabs, Space, Typography, 
  Alert, Spin, List, Upload, Progress, Badge, Drawer, Modal,
  Row, Col, Statistic, Timeline, Tag, Divider, message, Select,
  Form, Switch, InputNumber, Collapse
} from 'antd';
import {
  RobotOutlined, ToolOutlined, DashboardOutlined, SettingOutlined,
  FileTextOutlined, SendOutlined, UploadOutlined, DownloadOutlined,
  PlayCircleOutlined, StopOutlined, ReloadOutlined, DeleteOutlined,
  SearchOutlined, CodeOutlined, GlobalOutlined, BarChartOutlined,
  UserOutlined, BugOutlined, InfoCircleOutlined, QuestionCircleOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

// API base URL
const API_BASE_URL = 'http://localhost:8000';

// Ana component
const DeepResearchAgentUI = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [agentStatus, setAgentStatus] = useState({ is_initialized: false });
  const [systemInfo, setSystemInfo] = useState({});
  const [chatHistory, setChatHistory] = useState([]);
  const [taskHistory, setTaskHistory] = useState([]);
  const [currentTask, setCurrentTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [websocket, setWebsocket] = useState(null);

  // WebSocket bağlantısı
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket bağlantısı kuruldu');
      setWebsocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'result') {
        setChatHistory(prev => [...prev, {
          type: 'assistant',
          content: data.result,
          timestamp: data.timestamp
        }]);
        setLoading(false);
      } else if (data.type === 'error') {
        message.error(data.message);
        setLoading(false);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket bağlantısı kapandı');
    };
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Sistem durumunu yükle
  useEffect(() => {
    loadSystemStatus();
    loadSystemInfo();
    loadLogs();
  }, []);

  const loadSystemStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setAgentStatus(response.data);
    } catch (error) {
      console.error('Sistem durumu yüklenemedi:', error);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/info`);
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Sistem bilgisi yüklenemedi:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/logs?lines=50`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Loglar yüklenemedi:', error);
    }
  };

  const initializeAgent = async (configName = 'config_gemini') => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/agent/initialize?config_name=${configName}`);
      message.success('Agent başarıyla başlatıldı!');
      loadSystemStatus();
    } catch (error) {
      message.error('Agent başlatılamadı: ' + error.response?.data?.detail);
    }
    setLoading(false);
  };

  const resetAgent = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/agent/reset`);
      message.success('Agent sıfırlandı!');
      setAgentStatus({ is_initialized: false });
      setChatHistory([]);
      setTaskHistory([]);
    } catch (error) {
      message.error('Agent sıfırlanamadı: ' + error.response?.data?.detail);
    }
  };

  const sendMessage = async () => {
    if (!currentTask.trim() || !agentStatus.is_initialized) return;

    const userMessage = {
      type: 'user',
      content: currentTask,
      timestamp: new Date().toISOString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setLoading(true);

    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'task',
        task: currentTask
      }));
    } else {
      try {
        const response = await axios.post(`${API_BASE_URL}/agent/task`, {
          task: currentTask
        });
        
        setChatHistory(prev => [...prev, {
          type: 'assistant',
          content: response.data.result,
          timestamp: response.data.timestamp
        }]);
        
        setTaskHistory(prev => [...prev, response.data]);
      } catch (error) {
        message.error('Görev çalıştırılamadı: ' + error.response?.data?.detail);
      }
      setLoading(false);
    }

    setCurrentTask('');
  };

  const runTool = async (toolName, parameters) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/tools/run`, {
        tool_name: toolName,
        parameters: parameters
      });
      
      message.success('Araç başarıyla çalıştırıldı!');
      return response.data.result;
    } catch (error) {
      message.error('Araç çalıştırılamadı: ' + error.response?.data?.detail);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Sohbet arayüzü
  const ChatInterface = () => (
    <div style={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', backgroundColor: '#fafafa' }}>
        {chatHistory.map((message, index) => (
          <div key={index} style={{ marginBottom: '16px' }}>
            <Card 
              size="small"
              style={{
                marginLeft: message.type === 'user' ? '20%' : '0',
                marginRight: message.type === 'assistant' ? '20%' : '0',
                backgroundColor: message.type === 'user' ? '#e6f7ff' : '#f6ffed'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                {message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                <Text strong style={{ marginLeft: '8px' }}>
                  {message.type === 'user' ? 'Siz' : 'AI Agent'}
                </Text>
                <Text type="secondary" style={{ marginLeft: 'auto', fontSize: '12px' }}>
                  {new Date(message.timestamp).toLocaleTimeString('tr-TR')}
                </Text>
              </div>
              <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {message.content}
              </Paragraph>
            </Card>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>AI Agent düşünüyor...</div>
          </div>
        )}
      </div>
      
      <div style={{ padding: '16px', backgroundColor: '#fff', borderTop: '1px solid #f0f0f0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={currentTask}
            onChange={(e) => setCurrentTask(e.target.value)}
            placeholder="Mesajınızı yazın..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={!agentStatus.is_initialized}
          />
          <Button 
            type="primary" 
            icon={<SendOutlined />}
            onClick={sendMessage}
            disabled={!agentStatus.is_initialized || loading || !currentTask.trim()}
          >
            Gönder
          </Button>
        </Space.Compact>
        
        <div style={{ marginTop: '16px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            Örnek: "AI Agent konusundaki en son gelişmeleri araştır ve özetle"
          </Text>
        </div>
      </div>
    </div>
  );

  // Araçlar arayüzü
  const ToolsInterface = () => {
    const [selectedTool, setSelectedTool] = useState('deep_researcher');
    const [toolParams, setToolParams] = useState({});
    const [toolResult, setToolResult] = useState('');

    const tools = {
      deep_researcher: {
        name: 'Deep Researcher',
        icon: <SearchOutlined />,
        description: 'Kapsamlı web araştırması yapar',
        params: [
          { name: 'query', type: 'textarea', label: 'Araştırma Konusu', required: true }
        ]
      },
      deep_analyzer: {
        name: 'Deep Analyzer',
        icon: <BarChartOutlined />,
        description: 'Dosya ve veri analizi yapar',
        params: [
          { name: 'task', type: 'textarea', label: 'Analiz Görevi' },
          { name: 'source', type: 'input', label: 'Kaynak (URL/Dosya)' }
        ]
      },
      auto_browser: {
        name: 'Auto Browser',
        icon: <GlobalOutlined />,
        description: 'Otomatik web tarayıcı işlemleri',
        params: [
          { name: 'task', type: 'textarea', label: 'Tarayıcı Görevi', required: true }
        ]
      },
      python_interpreter: {
        name: 'Python Interpreter',
        icon: <CodeOutlined />,
        description: 'Python kodu çalıştırır',
        params: [
          { name: 'code', type: 'textarea', label: 'Python Kodu', required: true }
        ]
      }
    };

    const handleToolRun = async () => {
      const result = await runTool(selectedTool, toolParams);
      if (result) {
        setToolResult(result);
      }
    };

    return (
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="🔧 Araç Seçimi" size="small">
            <List
              dataSource={Object.entries(tools)}
              renderItem={([key, tool]) => (
                <List.Item
                  style={{
                    cursor: 'pointer',
                    backgroundColor: selectedTool === key ? '#e6f7ff' : 'transparent',
                    padding: '12px',
                    borderRadius: '6px'
                  }}
                  onClick={() => setSelectedTool(key)}
                >
                  <List.Item.Meta
                    avatar={tool.icon}
                    title={tool.name}
                    description={tool.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title={`⚙️ ${tools[selectedTool]?.name} Parametreleri`} size="small">
            <Form layout="vertical">
              {tools[selectedTool]?.params.map(param => (
                <Form.Item
                  key={param.name}
                  label={param.label}
                  required={param.required}
                >
                  {param.type === 'textarea' ? (
                    <TextArea
                      value={toolParams[param.name] || ''}
                      onChange={(e) => setToolParams(prev => ({
                        ...prev,
                        [param.name]: e.target.value
                      }))}
                      rows={3}
                    />
                  ) : (
                    <Input
                      value={toolParams[param.name] || ''}
                      onChange={(e) => setToolParams(prev => ({
                        ...prev,
                        [param.name]: e.target.value
                      }))}
                    />
                  )}
                </Form.Item>
              ))}
              
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleToolRun}
                loading={loading}
                block
              >
                Aracı Çalıştır
              </Button>
            </Form>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="📊 Sonuçlar" size="small">
            {toolResult ? (
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  {toolResult}
                </pre>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                Henüz sonuç yok
              </div>
            )}
          </Card>
        </Col>
      </Row>
    );
  };

  // Dashboard arayüzü
  const Dashboard = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Agent Durumu"
              value={agentStatus.is_initialized ? "Aktif" : "Pasif"}
              valueStyle={{
                color: agentStatus.is_initialized ? '#3f8600' : '#cf1322'
              }}
              prefix={agentStatus.is_initialized ? '✅' : '❌'}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Toplam Görev" value={taskHistory.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Sohbet Mesajları" value={chatHistory.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Mevcut Araçlar" value={systemInfo.tools?.length || 0} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="📝 Son Görevler" size="small">
            <List
              dataSource={taskHistory.slice(-5).reverse()}
              renderItem={(task, index) => (
                <List.Item>
                  <List.Item.Meta
                    title={`Görev ${taskHistory.length - index}`}
                    description={task.task?.substring(0, 100) + '...'}
                  />
                  <Badge status={task.status === 'completed' ? 'success' : 'error'} />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="📋 Sistem Logları" size="small">
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              <List
                dataSource={logs.slice(-10)}
                renderItem={(log) => (
                  <List.Item style={{ padding: '4px 0' }}>
                    <Text code style={{ fontSize: '11px' }}>{log}</Text>
                  </List.Item>
                )}
              />
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="📊 Sistem Bilgileri" size="small">
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <Card type="inner" title="🤖 Agentlar" size="small">
              <List
                dataSource={systemInfo.agents || []}
                renderItem={(agent) => (
                  <List.Item>
                    <Tag color="blue">{agent}</Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card type="inner" title="🔧 Araçlar" size="small">
              <List
                dataSource={systemInfo.tools || []}
                renderItem={(tool) => (
                  <List.Item>
                    <Tag color="green">{tool}</Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card type="inner" title="⚙️ Konfigürasyonlar" size="small">
              <List
                dataSource={systemInfo.configs || []}
                renderItem={(config) => (
                  <List.Item>
                    <Tag color="orange">{config}</Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card type="inner" title="🧠 Modeller" size="small">
              <List
                dataSource={systemInfo.models || []}
                renderItem={(model) => (
                  <List.Item>
                    <Tag color="purple">{model}</Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </Card>
    </Space>
  );

  // Ayarlar arayüzü
  const Settings = () => (
    <Row gutter={[16, 16]}>
      <Col span={12}>
        <Card title="🤖 Agent Ayarları" size="small">
          <Form layout="vertical">
            <Form.Item label="Konfigürasyon">
              <Select defaultValue="config_gemini" style={{ width: '100%' }}>
                {systemInfo.configs?.map(config => (
                  <Select.Option key={config} value={config}>{config}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item label="Varsayılan Model">
              <Select defaultValue="gemini-1.5-pro" style={{ width: '100%' }}>
                {systemInfo.models?.map(model => (
                  <Select.Option key={model} value={model}>{model}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item label="Maksimum Adım">
              <InputNumber min={1} max={50} defaultValue={20} style={{ width: '100%' }} />
            </Form.Item>
            
            <Form.Item label="Eşzamanlılık">
              <InputNumber min={1} max={10} defaultValue={4} style={{ width: '100%' }} />
            </Form.Item>
            
            <Form.Item>
              <Switch defaultChecked={false} />
              <span style={{ marginLeft: 8 }}>Yerel Proxy Kullan</span>
            </Form.Item>
          </Form>
        </Card>
      </Col>
      
      <Col span={12}>
        <Card title="🔧 Araç Ayarları" size="small">
          <Collapse>
            <Panel header="🔍 Deep Researcher" key="1">
              <Form layout="vertical" size="small">
                <Form.Item label="Maksimum Derinlik">
                  <InputNumber min={1} max={5} defaultValue={2} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item label="Maksimum İçgörü">
                  <InputNumber min={5} max={50} defaultValue={10} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item label="Zaman Limiti (saniye)">
                  <InputNumber min={30} max={300} defaultValue={120} style={{ width: '100%' }} />
                </Form.Item>
              </Form>
            </Panel>
            
            <Panel header="🌐 Web Arama" key="2">
              <Form layout="vertical" size="small">
                <Form.Item label="Arama Motoru">
                  <Select defaultValue="Google" style={{ width: '100%' }}>
                    <Select.Option value="Google">Google</Select.Option>
                    <Select.Option value="DuckDuckGo">DuckDuckGo</Select.Option>
                    <Select.Option value="Bing">Bing</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item label="Sonuç Sayısı">
                  <InputNumber min={1} max={20} defaultValue={5} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item label="Dil">
                  <Select defaultValue="tr" style={{ width: '100%' }}>
                    <Select.Option value="tr">Türkçe</Select.Option>
                    <Select.Option value="en">İngilizce</Select.Option>
                    <Select.Option value="auto">Otomatik</Select.Option>
                  </Select>
                </Form.Item>
              </Form>
            </Panel>
          </Collapse>
        </Card>
      </Col>
    </Row>
  );

  // Ana render
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        style={{ backgroundColor: '#001529' }}
      >
        <div style={{ 
          height: '32px', 
          margin: '16px', 
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 'bold'
        }}>
          {collapsed ? '🧠' : '🧠 DeepResearchAgent'}
        </div>
        
        <Menu 
          theme="dark" 
          defaultSelectedKeys={['chat']} 
          mode="inline"
          onClick={({ key }) => setActiveTab(key)}
        >
          <Menu.Item key="chat" icon={<RobotOutlined />}>
            Sohbet
          </Menu.Item>
          <Menu.Item key="tools" icon={<ToolOutlined />}>
            Araçlar
          </Menu.Item>
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
            Dashboard
          </Menu.Item>
          <Menu.Item key="settings" icon={<SettingOutlined />}>
            Ayarlar
          </Menu.Item>
        </Menu>
      </Sider>
      
      <Layout>
        <Header style={{ padding: '0 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                {activeTab === 'chat' && '💬 AI Agent ile Sohbet'}
                {activeTab === 'tools' && '🔧 Araç Yönetimi'}
                {activeTab === 'dashboard' && '📊 Sistem Dashboard'}
                {activeTab === 'settings' && '⚙️ Sistem Ayarları'}
              </Title>
            </Col>
            <Col>
              <Space>
                <Badge 
                  status={agentStatus.is_initialized ? 'processing' : 'error'} 
                  text={agentStatus.is_initialized ? 'Aktif' : 'Pasif'}
                />
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />}
                  onClick={() => initializeAgent()}
                  disabled={agentStatus.is_initialized}
                  loading={loading}
                >
                  Başlat
                </Button>
                <Button 
                  icon={<StopOutlined />}
                  onClick={resetAgent}
                  disabled={!agentStatus.is_initialized}
                >
                  Sıfırla
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    loadSystemStatus();
                    loadSystemInfo();
                    loadLogs();
                  }}
                >
                  Yenile
                </Button>
              </Space>
            </Col>
          </Row>
        </Header>
        
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'tools' && <ToolsInterface />}
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'settings' && <Settings />}
        </Content>
      </Layout>
    </Layout>
  );
};

export default DeepResearchAgentUI;
