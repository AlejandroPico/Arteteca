import { mount } from 'svelte';
import App from './App.svelte';
import './app.scss';
import './lib/pwa';
import { applyThemeToDocument, readStoredCoordinates, readStoredTheme } from './lib/solarTheme';

applyThemeToDocument(readStoredTheme(), new Date(), readStoredCoordinates());

const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
