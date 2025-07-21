import React from 'react';
import { Outlet } from 'react-router';

import {Footer, Header} from "../components";
import {App} from "../components/App/App";
import  css from "./MainLayout.module.css";
import { useAppSelector } from '../hooks/'; 

const MainLayout = () => {

   const theme = useAppSelector((state) => state.theme.theme);
   
    return (
        <div className={theme ? css.MainLayoutLight : css.MainLayoutDark}>
            <Header/>
            <Outlet/>
            <Footer/>
        </div>
    );
};

export {MainLayout};