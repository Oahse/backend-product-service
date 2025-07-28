import ksuid

class Generator:
    def __init__(self):
        pass

    def get_id(self):
        return ksuid.ksuid()

# print(generate_ksuid())  # e.g., 1ksuid2xkl2jrl0fjqz7fqdtx7q


generator = Generator()
# print(generator.get_id())

