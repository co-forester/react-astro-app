// import React from 'react';
// import {Outlet} from "react-router-dom";

// import css from './style.module.css'
// import {useAppSelector } from '../../hooks/reduxHook.ts';

// const App = () => {
//     const theme = useAppSelector(state => state.theme.theme);
//     return (
//         <div className={theme ? css.AppLight : css.AppDark}>
//             <Outlet/>
//         </div>
//     );
// };

// export {App};

import React from 'react';
import {Outlet} from "react-router-dom";

import { useAppSelector } from '../../hooks/reduxHook';
import  css from './app.module.css';

const App = () => {

    const theme = useAppSelector(state => state.theme.theme);
   
    return (
        <div className={(theme )? css.AppLight : css.AppDark}>
            <Outlet/>
        </div>
    );
};

export {App};
