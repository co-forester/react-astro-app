import React from 'react';
import ReactDOM from 'react-dom/client';
import {RouterProvider} from "react-router-dom";
import {Provider} from "react-redux";
import { injectSpeedInsights } from "@vercel/speed-insights";

injectSpeedInsights();

import './index.css';
import {router} from "./router";
import {store} from "./redux";

 console.log("router:", router);
 console.log("store:", store);


const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <Provider store={store}>
    <RouterProvider router={router} />
  </Provider>
);


