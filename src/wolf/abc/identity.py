from authsources.identity import User


class AnonymousUser(User):
    id = -1
    data = None


anonymous = AnonymousUser()
