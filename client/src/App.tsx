import '@mantine/core/styles.css'
import { HeaderSimple } from './components/HeaderSimple'
import { FeaturesTitle } from './components/FeaturesTitle'
import { Inference } from './components/Inference'
import { PreviousSearches } from './components/PreviousSearches'

function App() {

    return (
        <>
            <HeaderSimple />
            <FeaturesTitle />
            <Inference />
            <PreviousSearches />
        </>
    )
}

export default App
