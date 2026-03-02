from convosaver import ConvoSaver, MySQLConfig, MySQLStore


def main() -> None:
    config = MySQLConfig(url="mysql+pymysql://convosaver:convosaverpass@127.0.0.1:3306/convosaver")
    store = MySQLStore(config)
    saver = ConvoSaver(store)

    conversation_id = saver.start(metadata={"team": "hackathon"})
    saver.add_message(conversation_id, role="user", content="Hello")
    saver.add_message(conversation_id, role="assistant", content="Hi from MySQL")

    conversation = saver.get(conversation_id)
    print(conversation.id, len(conversation.messages))


if __name__ == "__main__":
    main()
