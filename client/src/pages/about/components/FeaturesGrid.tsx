import { ThemeIcon, Text, Title, Container, SimpleGrid, rem } from '@mantine/core';
import classes from './FeaturesGrid.module.css';

interface FeatureProps {
    icon: React.FC<any>;
    title: React.ReactNode;
    description: React.ReactNode;
}

export function Feature({ icon: Icon, title, description }: FeatureProps) {
    return (
        <div>
            <ThemeIcon variant="light" size={40} radius={40}>
                <Icon style={{ width: rem(18), height: rem(18) }} stroke={1.5} />
            </ThemeIcon>
            <Text mt="sm" mb={7}>
                {title}
            </Text>
            <Text size="sm" c="dimmed" lh={1.6}>
                {description}
            </Text>
        </div>
    );
}

export function FeaturesGrid() {
    return (
        <Container className={classes.wrapper}>
            <Title className={classes.title}>Project Description</Title>
            <Container size={800} p={0}>
                <Text size="md" className={classes.description}>
                    In response to the escalating threat landscape of cyber attacks, we are at the forefront of a pioneering 
                    initiative that leverages advanced technologies to address the surge in malicious websites. 
                    Our strategic approach involves deploying cutting-edge machine learning, natural language processing (NLP), 
                    and image recognition algorithms. <br/><br/>
                    At the core of this project is the development of a sophisticated machine-learning model, 
                    meticulously designed for the early identification of malicious sites.
                </Text>
            </Container>
        </Container>
    );
}
