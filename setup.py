from setuptools import setup

test_requirements = [
    'pytest',
    'pytest-cov',
    'coveralls',
    'mock',
    'numpy',

    # Only their Exceptions
    'setuptools',
    'psutil',
    'requests'
]

setup(
    name='nginx-amplify-agent-health-check',
    version='0.1.3',
    description='Static and Dynamic Analysis for nginx-amplify-agent Health Status',
    url='https://github.com/hiradyazdan/nginx-amplify-agent-health-check',
    author='Hirad Yazdanpanah',
    author_email='hirad.y@gmail.com',
    license='MIT',
    packages=['amplifyhealthcheck'],
    install_requires=[
        'psutil',
        'setuptools',
        'ntplib',
        'crossplane',
        'requests'
    ],
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    extras_require={
        'test': test_requirements,
    },
    zip_safe=False
)
