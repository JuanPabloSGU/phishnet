import { Table, Text, Container, Title } from '@mantine/core';
import classes from './PreviousSearches.module.css';
import { useEffect, useState } from 'react'

type URL = {
    url: string;
    model: string;
    value: Array<Number>;
}

export function PreviousSearches() {
    const [urls, setloadUrls] = useState<URL[]>([])
    var history = localStorage.getItem('urls');

    useEffect(() => {
        if (history !== null) {
            setloadUrls(JSON.parse(history))
        }
    }, []);

    const rows = urls.map((row: URL) => {
        return (
            <Table.Tr key={row.url}>
                <Table.Td>
                    {row.url}
                </Table.Td>
                <Table.Td>
                    {row.model}
                </Table.Td>
                <Table.Td>
                    {typeof row.value[0] === 'number' ? (row.value[0] * 100).toFixed(2) : 'N/A'}%
                </Table.Td>
            </Table.Tr>
        )
    })

    return (
        <Container className={classes.container}>
            <Title>
                Previous Searches
            </Title>

            <Text c='dimmed'>
                Lorem ipsum dolor sit amet, qui minim labore adipisicing minim sint cillum sint consectetur cupidatat.
            </Text>

            <Table.ScrollContainer minWidth={800}>
                <Table verticalSpacing="xs">
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>URL</Table.Th>
                            <Table.Th>Model</Table.Th>
                            <Table.Th>Verdict</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>{rows}</Table.Tbody>
                </Table>
            </Table.ScrollContainer>
        </Container>
    );
}
