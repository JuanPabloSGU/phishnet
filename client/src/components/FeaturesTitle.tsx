import { Title, Text, Grid, Container } from '@mantine/core';
import classes from './FeaturesTitle.module.css';


export function FeaturesTitle() {
    return (
        <Container className={classes.container}>
            <div>
                <Grid gutter={80}>
                    <Grid.Col span={12}>
                        <Title className={classes.title} order={2}></Title>
                        <Text>
                            Welcome to Phishnet, your go-to platform for determining the legitimacy of URLs and safeguarding yourself against phishing attempts.
                        </Text>
                    </Grid.Col>
                </Grid>
            </div>
        </Container>
    );
}
