import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import '@mantine/core/styles.css'

import { MantineProvider, createTheme, MantineColorsTuple } from '@mantine/core'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import Contact from './pages/contact/Contact.tsx'
import About from './pages/about/About.tsx'
import Login from './pages/login/Login.tsx'

const colours: MantineColorsTuple = [
    "#f3edff",
    "#e0d7fa",
    "#beabf0",
    "#9a7ce6",
    "#7c56de",
    "#683dd9",
    "#5f2fd8",
    "#4f23c0",
    "#451eac",
    "#3a1899"
]

const theme = createTheme({
    colors: {
        colours,
    }
});


const router = createBrowserRouter([
    {
        path: "/",
        element: <App />
    },
    {
        path: "/contact",
        element: <Contact />
    },
    {
        path: "/about",
        element: <About />
    },
    {
        path: "/login",
        element: <Login />
    }
])

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <MantineProvider theme={theme}>
            <RouterProvider router={router} />
        </MantineProvider>
    </React.StrictMode>,
)
