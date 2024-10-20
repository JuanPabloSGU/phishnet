import { Container, Group } from '@mantine/core';
import { Link } from 'react-router-dom';
import classes from './index.module.css';

const links = [
    { link: '/about', label: 'About' },
    { link: '/contact', label: 'Contact' },
    { link: '/login', label: 'Login' },
];

const Footer = () => {
    const items = links.map((link) => (
        <Link
            className={`dimmed ${classes.links}`}
            key={link.label}
            to={link.link}
        >
            {link.label}
        </Link>
    ));

    return (
        <div className={classes.footer}>
            <Container className={classes.inner}>
                <h2>Phishnet</h2>
                <Group className={classes.links}>{items}</Group>
            </Container>
        </div>
    );
}

export default Footer;
