import {
  Button,
  Container,
  Paper,
  SegmentedControl,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useState } from "react";
import classes from "./index.module.css";
import axios from "axios";
import InferenceResult from "@components/InferenceResult";
import { useAuth } from "@context/Auth";

type Triton = {
  url: string;
  model: string;
  value: Array<number>;
  message: string;
};

const models = [
  { label: "Logistic Regression", value: "/logres" },
  { label: "Random Forest", value: "/randforest" },
  { label: "Multi-layer Perceptron", value: "/mlp" },
];

export function Inference() {
  const [url, setUrl] = useState("");
  const [model, setModel] = useState("/logres");
  const [resultStream, setResultStream] = useState<Triton>();
  const [invalidURL, isInvalidURL] = useState("");
  const { userInfo } = useAuth();
 
  const handleInferece = () => {
    if (url === "") {
      return;
    }

    const target = "https://api.capstone.databending.ca/api/v1" + model;

    const token = userInfo?.id_token;

    console.log(userInfo?.id_token)
    axios({
      method: "post",
      url: target,
      data: {
        url: url,
      },
      headers: {
        Authorization: "Bearer " + token,
      },
    })
      .then(function(response) {
        const result = response.data["triton"]["outputs"][0]["data"];
        let msg = "";

        if (result > 0.5) {
          msg = "Malicious website!";
        } else {
          msg = "Non Malicious website!";
        }

        const data = {
          url: response.data["url"],
          model: models.find((item) => item.value === model)?.label || "",
          value: result,
          message: msg,
        };

        setResultStream(data);
        isInvalidURL("");

        const previous_urls = localStorage.getItem("urls");
        if (previous_urls === null) {
          const urls = [];
          urls.push(data);
          localStorage.setItem("urls", JSON.stringify(urls));
          return;
        }

        const list: Array<object> = JSON.parse(previous_urls);
        list.push(data);

        localStorage.setItem("urls", JSON.stringify(list));
      })
      .catch(function(error) {
        console.log(error);
        isInvalidURL("URL is invalid");
      });
  };

  return (
    <Container className={classes.container}>
      <Title>
        Scan
      </Title>

      <Text c="dimmed">
        Our advanced scanning tool employs machine learning to analyze URLs and
        distinguish between legitimate websites and potential phishing threats.
        Enter a URL below to instantly assess its authenticity:
      </Text>

      <Paper>
        <div className={classes.control}>
          <div className={classes.input}>
            <TextInput
              className={classes.box}
              error={invalidURL}
              placeholder="Enter a URL, e.g. https://example.com"
              value={url}
              onChange={(event) => setUrl(event.currentTarget.value)}
              required
            />
            <Button onClick={handleInferece}>
              Submit
            </Button>
          </div>
          <SegmentedControl
            radius="md"
            value={model}
            onChange={setModel}
            size="sm"
            data={models}
          />
        </div>
      </Paper>

      <div>
        {resultStream ? <InferenceResult props={resultStream} /> : <div></div>}
      </div>
    </Container>
  );
}

export default Inference;
