import { createApp } from 'vue';
import App from './App.vue';
import { getPluginBridge } from './lib/pluginBridge';
import './styles.css';

async function bootstrap(): Promise<void> {
  await getPluginBridge().ready();
  createApp(App).mount('#app');
}

void bootstrap();
