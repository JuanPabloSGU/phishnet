import { Button, Paper, Text, Title } from "@mantine/core";
import classes from "./index.module.css";

import { useAuth } from "@context/Auth";
import { Navigate } from "react-router-dom";

const Login = () => {
  const { login, authenticated } = useAuth();

  if (authenticated) {
    return <Navigate to="/login/callback" />;
  }

  return (
    <div className={classes.wrapper}>
      <Paper className={classes.form} radius={0} p={30}>
        <Title order={2} className={classes.title} ta="center" mt="md">
          Login to your account
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
          Login Now
        </Button>
      </Paper>
    </div>
  );
};
export default Login;
