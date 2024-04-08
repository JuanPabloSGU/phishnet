import { Avatar, Badge, Table, Group, Text, Anchor } from '@mantine/core';

const data = [
    {
        name: 'Alfred Genadri',
        job: 'Engineer',
        email: 'agena036@uottawa.ca',
    },
    {
        name: 'Adam Jasniewicz',
        job: 'Engineer',
        email: 'ajasn076@uottawa.ca',
    },
    {
        name: 'Arunav Sinha',
        job: 'Engineer',
        email: 'asinh060@uottawa.ca',
    },
    {
        name: 'James Couture',
        job: 'Designer',
        email: 'jcout071@uottawa.ca',
    },
    {
        name: 'Juan Pablo Sanchez Garcia',
        job: 'Manager',
        email: 'jsanc016@uottawa.ca',
    },
];

const jobColors: Record<string, string> = {
    engineer: 'blue',
    manager: 'cyan',
    designer: 'pink',
};

export function TeamTable() {
    const rows = data.map((item) => (
        <Table.Tr key={item.name}>
            <Table.Td>
                <Group gap="sm">
                    <Avatar size={30} radius={30} />
                    <Text fz="sm" fw={500}>
                        {item.name}
                    </Text>
                </Group>
            </Table.Td>

            <Table.Td>
                <Badge color={jobColors[item.job.toLowerCase()]} variant="light">
                    {item.job}
                </Badge>
            </Table.Td>
            <Table.Td>
                <Anchor component="button" size="sm">
                    {item.email}
                </Anchor>
            </Table.Td>
        </Table.Tr>
    ));

    return (
        <Table.ScrollContainer minWidth={800}>
            <Table verticalSpacing="sm">
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>Employee</Table.Th>
                        <Table.Th>Job title</Table.Th>
                        <Table.Th>Email</Table.Th>
                        <Table.Th />
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>{rows}</Table.Tbody>
            </Table>
        </Table.ScrollContainer>
    );
}
