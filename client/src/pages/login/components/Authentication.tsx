import {
    Paper,
    TextInput,
    PasswordInput,
    Button,
    Title,
    Text,
} from '@mantine/core';
import classes from './Authentication.module.css';
import { useState } from 'react';
import axios from 'axios';
import { redirect } from 'react-router-dom';

export function Authentication() {
    const [user, setUser] = useState('');
    const [pass, setPass] = useState('');
    const [validUser, isValidUser] = useState('');
    const [validPass, isValidPass] = useState('');

    const handleLogin = () => {
        if (user === '') {
            isValidUser('Invalid username')
            return
        }

        if (pass === '') {
            isValidPass('Invalid password')
            return
        }

        axios.post('http://localhost:5000/api/v1/login', {
            username: user,
            password: pass
        })
            .then(function(response) {
                var token = response.data["access_token"]
                localStorage.setItem('jwt', token)
                isValidUser('')
                isValidPass('')

                return redirect("/")
            })
            .catch(function(error) {
                console.log(error)
            })

    }

    return (
        <div className={classes.wrapper}>
            <Paper className={classes.form} radius={0} p={30}>
                <Title order={2} className={classes.title} ta="center" mt="md">
                    Login
                </Title>

                <Text c="dimmed" size="sm" ta="center" mt={5} mb={30}>
                    Lorem ipsum dolor sit amet, qui minim labore adipisicing minim sint cillum sint consectetur cupidatat.
                </Text>

                <TextInput
                    label="Username"
                    placeholder="hello@gmail.com"
                    value={user}
                    onChange={(event) => setUser(event.currentTarget.value)}
                    size="md"
                    error={validUser}
                />
                <PasswordInput
                    label="Password"
                    placeholder="Your password"
                    value={pass}
                    onChange={(event) => setPass(event.currentTarget.value)}
                    mt="md"
                    size="md"
                    error={validPass}
                />
                <Button
                    fullWidth
                    mt="xl"
                    size="md"
                    onClick={handleLogin}
                >
                    Login
                </Button>
            </Paper>
        </div>
    );
}
