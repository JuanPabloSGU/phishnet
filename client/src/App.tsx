import "@mantine/core/styles.css";
import { HeaderSimple } from "./components/HeaderSimple";
import { FeaturesTitle } from "./components/FeaturesTitle";
import { Inference } from "./components/Inference";
import { PreviousSearches } from "./components/PreviousSearches";
import { FooterSimple } from "./components/FooterSimple";

function App() {
  return (
    <>
      <HeaderSimple />
      <FeaturesTitle />
      <Inference />
      <PreviousSearches />
      <FooterSimple />
    </>
  );
}

export default App;
