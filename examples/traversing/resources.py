import pathlib
from wolf.services.resources import Library, DiscoveryLibrary

here = pathlib.Path(__file__).parent.resolve()


my_super_lib = Library('somelib', here / "static" / "top_lib")
dep = my_super_lib.bind('dep.js')

my_lib = Library('reha', here / "static" / "example")
whatever = my_lib.bind('lib.js', dependencies=[dep])
somejs = my_lib.bind('some.js', dependencies=[whatever])


static = DiscoveryLibrary(
    'misc', here / 'static' / 'misc', restrict=("*.jpg", "*.ico"))
