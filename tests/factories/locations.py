import factory


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'locations.Department'

    code = factory.Sequence(lambda n: f'{n:06d}')
    name = factory.Faker('city')


class ProvinceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'locations.Province'

    code = factory.Sequence(lambda n: f'{n:06d}')
    name = factory.Faker('city')
    department = factory.SubFactory(DepartmentFactory)


class DistrictFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'locations.District'

    code = factory.Sequence(lambda n: f'{n:06d}')
    name = factory.Faker('city')
    province = factory.SubFactory(ProvinceFactory)


class PopulatedCenterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'locations.PopulatedCenter'

    code = factory.Sequence(lambda n: f'{n:010d}')
    name = factory.Faker('city')
    type = 'rural'
    district = factory.SubFactory(DistrictFactory)
