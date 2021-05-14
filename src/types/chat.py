class ChatId(int):
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, int):
            raise TypeError('integer required')
        if v.bit_length() > 64:
            raise TypeError('Chat ID bigger than int 64')

        return cls(v)
