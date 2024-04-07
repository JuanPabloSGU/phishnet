import { useState } from 'react';
import { Container, Group } from '@mantine/core';
import classes from './HeaderSimple.module.css';
import { Link } from 'react-router-dom';

const links = [
    { link: '/about', label: 'About' },
    { link: '/contact', label: 'Contact' },
];

export function HeaderSimple() {
    const [active, setActive] = useState(links[0].link);

    const items = links.map((link) => (
        <a
            key={link.label}
            href={link.link}
            className={classes.link}
            data-active={active === link.link || undefined}
            onClick={(event) => {
                event.preventDefault();
                setActive(link.link);
            }}
        >
            <Link to={link.link} className={classes.link}>
                {link.label}
            </Link>
        </a>
    ));

    return (
        <header className={classes.header}>
            <Container size="md" className={classes.inner}>
                <h2>Phishnet</h2>
                <Group gap={5} visibleFrom="xs">
                    {items}
                </Group>
            </Container>
        </header>
    );
}
