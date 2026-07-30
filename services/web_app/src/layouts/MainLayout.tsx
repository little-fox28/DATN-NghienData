import React from 'react';
import { Layout, Menu, theme } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { DashboardOutlined, FormOutlined } from '@ant-design/icons';
import { Navbar } from '../components/Navbar';
import { useTranslation } from 'react-i18next';
import { useAppContext } from '../contexts/AppProvider';

const { Content, Footer, Sider } = Layout;

export const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const { isDarkMode } = useAppContext();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Navbar />
      <Layout>
        <Sider width={250} theme={isDarkMode ? 'dark' : 'light'} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            style={{ height: '100%', borderRight: 0, paddingTop: 16 }}
            onClick={({ key }) => navigate(key)}
            items={[
              {
                key: '/',
                icon: <DashboardOutlined />,
                label: t('menu.dashboard'),
              },
              {
                key: '/apply',
                icon: <FormOutlined />,
                label: t('menu.apply'),
              }
            ]}
          />
        </Sider>
        <Layout style={{ padding: '24px 24px 24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {/* The Outlet renders the child routes */}
            <Outlet />
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            {t('footer.copyright')}
          </Footer>
        </Layout>
      </Layout>
    </Layout>
  );
};
