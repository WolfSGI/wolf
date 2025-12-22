from wolf.annotations import annotation


class example(annotation):
    name = "__example__"

    def __init__(self, name: str, title: str):
        super().__init__(name=name, title=title)


def test_example_annotation():

    class MyClass:

        @example('whatever', 'This is Whatever')
        def whatever(self):
            pass

        @example('another', 'This is yet Another')
        def another(self):
            pass

        def not_annotated(self):
            pass

    annotations = example.find(MyClass)
    assert list(annotations) == [
        ({'name': 'another', 'title': 'This is yet Another'},
        MyClass.another),
        ({'name': 'whatever', 'title': 'This is Whatever'},
        MyClass.whatever,)
    ]
