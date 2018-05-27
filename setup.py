from setuptools import setup

classifiers = [
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX'
] + [
    ('Programming Language :: Python :: %s' % x)
    for x in '2.7'.split()
]

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

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='nginx-amplify-agent-health-check',
    version='0.1.4',
    description='Static and Dynamic Analysis for nginx-amplify-agent Health Status',
    long_description=long_description,
    url='https://github.com/hiradyazdan/nginx-amplify-agent-health-check',
    author='Hirad Yazdanpanah',
    author_email='hirad.y@gmail.com',
    license='MIT',
    platforms=["linux"],
    packages=['amplifyhealthcheck'],
    entry_points={
        'console_scripts': [
            'amphc=amplifyhealthcheck.cmd:main'
        ]
    },
    classifiers=classifiers,
    keywords="nginx amplify nginx-amplify nginx-configuration health-check metrics",
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
    python_requires='==2.7.*',
    zip_safe=False
)
