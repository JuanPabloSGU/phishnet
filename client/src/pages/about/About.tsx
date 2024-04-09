import '@mantine/core/styles.css'
import { HeaderSimple } from '../../components/HeaderSimple'
import { FooterSimple } from '../../components/FooterSimple'
import { Container } from '@mantine/core'
import { FeaturesGrid } from './components/FeaturesGrid'

function About() {
    return (
        <>
            <HeaderSimple />
            <Container>
                <FeaturesGrid />
            </Container>

            <FooterSimple />
        </>
    )
}

export default About
