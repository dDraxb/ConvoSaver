from convosaver import ConvoSaver, MySQLConfig, MySQLStore, ConversationPolicy


def main() -> None:
    config = MySQLConfig(url="mysql+pymysql://convosaver:convosaverpass@127.0.0.1:3306/convosaver")
    store = MySQLStore(config)
    policy = ConversationPolicy(max_messages=10, max_chars=500)
    saver = ConvoSaver(store, policy=policy)

    conversation_id = saver.start(metadata={"source": "example"})

    saver.add_message(conversation_id, role="user", content="Hello")
    saver.add_message(conversation_id, role="assistant", content="Hi! How can I help?")

    conversation = saver.get(conversation_id)
    print(conversation.id, len(conversation.messages))


if __name__ == "__main__":
    main()
