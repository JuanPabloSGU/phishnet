import { Text, Card, RingProgress, useMantineTheme, Container } from '@mantine/core';
import classes from './InferenceResult.module.css'


type Triton = {
    props: {
        url: string;
        value: Array<Number>;
        message: string;
    }
};

export function InferenceResult(props: Triton) {
    const theme = useMantineTheme();
    var url = props.props.url;
    var value = Number(props.props.value[0]);
    var message = props.props.message;

    return (
        < Container className={classes.container} >
            <Card withBorder p="xl" radius="md" className={classes.card}>
                <div className={classes.inner}>
                    <div>
                        <Text fz="xl" className={classes.label}>
                            Your Request
                        </Text>
                        <div>
                            <Text className={classes.lead} mt={30}>
                                URL searched: {url}
                            </Text>
                        </div>
                    </div>

                    <div className={classes.ring}>
                        <RingProgress
                            roundCaps
                            thickness={6}
                            size={200}
                            sections={[{ value: (value) * 100, color: theme.primaryColor }]}
                            label={
                                <div>
                                    <Text ta="center" fz="lg" className={classes.label}>
                                        {((value) * 100).toFixed(0)}%
                                    </Text>
                                    <Text ta="center" fz="xs" c="dimmed">
                                        {message}
                                    </Text>
                                </div>
                            }
                        />
                    </div>
                </div>
            </Card>
        </Container >
    );
}
