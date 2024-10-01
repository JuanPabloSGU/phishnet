import {
  Button,
  Paper,
  Text,
  Title,
} from "@mantine/core";
import classes from "./Authentication.module.css";

import { useAuth } from "../../context/Auth/Auth.provider";
import { Navigate } from "react-router-dom";

export function Authentication() {
  const { login, authenticated } = useAuth();

  if (authenticated) {
    return <Navigate to="/login/callback" />;
  }

  return (
    <div className={classes.wrapper}>
      <Paper className={classes.form} radius={0} p={30}>
        <Title order={2} className={classes.title} ta="center" mt="md">
          Login
        </Title>

        <Text c="dimmed" size="sm" ta="center" mt={5} mb={30}>
          Access your account.
        </Text>


        <Button
          fullWidth
          mt="xl"
          size="md"
          onClick={login}
        >
          Login
        </Button>

      </Paper>
    </div>
  );
}
