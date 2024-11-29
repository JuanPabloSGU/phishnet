import { useAuth } from "@context/Auth";
import { ActionIcon, Button, Flex, Text, TextInput } from "@mantine/core";
import { IconCheck } from "@tabler/icons-react";
const Callback = () => {
  const { authenticated, userInfo, signout } = useAuth();

  if (authenticated === true && userInfo) {
    return (
      <div className="user">
        <h2>Welcome, {userInfo.profile.name}!</h2>
        <TextInput disabled label="Name" value={userInfo.profile.name} />
        <TextInput disabled label="Email" value={userInfo.profile.email} />
        <Flex mt={4} mb="lg" align="center">
          <Text size="sm" mr={5}>Email Verified</Text>
          <ActionIcon
            variant="filled"
            size="sm"
            radius="xl"
            color="green"
            aria-label="Settings"
          >
            <IconCheck style={{ width: "90%", height: "90%" }} stroke={2} />
          </ActionIcon>
        </Flex>

        <Button onClick={signout}>Log out</Button>
      </div>
    );
  } else {
    return <div>Loading...</div>;
  }
};

export default Callback;
