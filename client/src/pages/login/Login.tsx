import '@mantine/core/styles.css'
import { Authentication } from './components/Authentication'
import { HeaderSimple } from '../../components/HeaderSimple'
import { Container } from '@mantine/core'

function Login() {
    return (
        <>
            <HeaderSimple />
            <Container>
                <Authentication />
            </Container>
        </>
    )
}

export default Login
