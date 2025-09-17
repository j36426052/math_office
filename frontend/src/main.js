import { createApp } from 'vue'
import './style.css'
import './theme.css'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import RoomsPage from './pages/RoomsPage.vue'
import RoomDetailPage from './pages/RoomDetailPage.vue'
import AdminPage from './pages/AdminPage.vue'

const routes = [
  { path: '/', component: RoomsPage },
  { path: '/rooms/:id', component: RoomDetailPage, props: true },
  // 管理路由暫時隱藏
  { path: '/admin', component: AdminPage },
]

const router = createRouter({ history: createWebHistory(), routes })

createApp(App).use(router).mount('#app')
