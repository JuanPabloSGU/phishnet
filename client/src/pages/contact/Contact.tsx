import '@mantine/core/styles.css'
import { HeaderSimple } from '../../components/HeaderSimple'
import { FooterSimple } from '../../components/FooterSimple'
import { Container } from '@mantine/core'
import { TeamTable } from './components/TeamTable'

function Contact() {
    return (
        <>
            <HeaderSimple />
            <Container>
                <TeamTable />
            </Container>
            <FooterSimple />
        </>
    )
}

export default Contact
