import { Button, Container, Paper, SegmentedControl, Text, TextInput, Title } from "@mantine/core"
import { useState } from 'react'
import classes from './Inference.module.css'
import axios from "axios";
import { InferenceResult } from "./InferenceResult";

type Triton = {
    url: string;
    model: string;
    value: Array<Number>;
    message: string;
};

const models = [
    { label: 'Logistic Regression', value: '/logres' },
    { label: 'Random Forest', value: '/randforest' },
    { label: 'Multi-layer Perceptron', value: '/mlp' },
]


export function Inference() {
    const [url, setUrl] = useState('');
    const [model, setModel] = useState('/logres');
    const [resultStream, setResultStream] = useState<Triton>();
    const [invalidURL, isInvalidURL] = useState('');

    const handleInferece = () => {
        if (url === '') {
            return
        }

        var target = 'http://localhost:5000/api/v1' + model

        var token = localStorage.getItem('jwt')

        axios({
            method: 'post',
            url: target,
            data: {
                url: url
            },
            headers: {
                Authorization: 'Bearer ' + token
            }
        })
            .then(function(response) {
                var result = response.data["triton"]["outputs"][0]["data"]
                var msg = ""

                if (result > 0.5) {
                    msg = "Malicious website!"

                } else {
                    msg = "Non Malicious website!"
                }

                var data = {
                    url: response.data["url"],
                    model: models.find(item => item.value === model)?.label || '',
                    value: result,
                    message: msg
                }

                setResultStream(data)
                isInvalidURL('')

                var previous_urls = localStorage.getItem('urls');
                if (previous_urls === null) {
                    var urls = [];
                    urls.push(data)
                    localStorage.setItem('urls', JSON.stringify(urls))
                    return
                }

                var list: Array<Object> = JSON.parse(previous_urls)
                list.push(data)

                localStorage.setItem('urls', JSON.stringify(list))
            })
            .catch(function(error) {
                console.log(error)
                isInvalidURL('URL is invalid')
            })
    };

    return (
        <Container className={classes.container}>
            <Title>
                Scan
            </Title>

            <Text c='dimmed'>
                Lorem ipsum dolor sit amet, qui minim labore adipisicing minim sint cillum sint consectetur cupidatat.
            </Text>

            <Paper>
                <div className={classes.control}>
                    <div className={classes.input}>
                        <TextInput className={classes.box}
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
                    <SegmentedControl radius="md"
                        value={model}
                        onChange={setModel}
                        size="sm"
                        data={models} />
                </div>

            </Paper>

            <div>
                {resultStream ? <InferenceResult props={resultStream} /> : <div></div>}
            </div>
        </Container >
    )
}

