import '@mantine/core/styles.css'
import { Authentication } from './components/Authentication'
import { HeaderSimple } from '../../components/HeaderSimple'
import { Container } from '@mantine/core'
import { FooterSimple } from '../../components/FooterSimple'

function Login() {
    return (
        <>
            <HeaderSimple />
            <Container>
                <Authentication />
            </Container>
            <FooterSimple />
        </>
    )
}

export default Login
