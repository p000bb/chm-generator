import "./style.scss";
import "./demos/ipc";

import App from "./App.vue";
import { createApp } from "vue";
import router from "./router";

// If you want use Node.js, the`nodeIntegration` needs to be enabled in the Main process.
// import './demos/node'

createApp(App)
  .use(router)
  .mount("#app")
  .$nextTick(() => {
    postMessage(
      {
        payload: "removeLoading",
      },
      "*"
    );
  });
