# Contributing to HTTPTests

Thank you for your interest in contributing to HTTPTests! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Docker version, GitHub Actions runner)
- Relevant logs or error messages

### Suggesting Features

We love feature suggestions! Please create an issue with:
- A clear description of the feature
- Use case and motivation
- Example implementation (if applicable)
- Any potential drawbacks or considerations

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, descriptive commits
3. **Add tests** if you're adding functionality
4. **Update documentation** if you're changing behavior
5. **Ensure tests pass** by running the test suite
6. **Submit a pull request** with a clear description

#### Pull Request Guidelines

- Keep PRs focused on a single issue or feature
- Write clear commit messages
- Update the CHANGELOG.md for notable changes
- Follow the existing code style
- Add examples if introducing new features

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/serviceguards-com/httptests-action.git
cd httptests-action
```

2. Make your changes to the action files:
   - `action.yml` - GitHub Action definition
   - `main.py` - Test runner
   - `generate_docker_compose.py` - Docker Compose generator

3. Test locally using the example:
```bash
cd ../httptests-example
python ../httptests-action/generate_docker_compose.py --suite ./.httptests --output ./.httptests/docker-compose.yml
docker compose -f ./.httptests/docker-compose.yml up -d
python ../httptests-action/main.py --test-file ./.httptests/test.json
docker compose -f ./.httptests/docker-compose.yml down -v
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **YAML**: Use 2-space indentation
- **Markdown**: Use consistent formatting
- **Comments**: Write clear, helpful comments

### Testing

Before submitting a PR:
- Test the action with the provided examples
- Ensure all existing examples still work
- Add new examples for new features
- Test on a GitHub Actions runner if possible

### Documentation

- Update README.md for user-facing changes
- Update TECHNICAL.md for technical details
- Add examples for new features
- Keep code comments up to date

## Community Guidelines

### Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

### Getting Help

- **Documentation**: Check [TECHNICAL.md](TECHNICAL.md) first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Examples**: Look at the [httptests-example repository](https://github.com/serviceguards-com/httptests-example)

## Recognition

Contributors will be:
- Listed in release notes
- Mentioned in the CHANGELOG
- Credited in the repository

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to create an issue for any questions about contributing!

---

Thank you for helping make HTTPTests better!

