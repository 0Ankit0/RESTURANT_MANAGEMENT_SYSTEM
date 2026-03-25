module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat', // New feature
        'fix', // Bug fix
        'docs', // Documentation
        'style', // Formatting, missing semicolons, etc.
        'refactor', // Code refactoring
        'perf', // Performance improvements
        'test', // Adding tests
        'chore', // Maintenance tasks
        'revert', // Reverting changes
        'ci', // CI/CD changes
        'build', // Build system changes
      ],
    ],
    'subject-case': [2, 'always', 'lower-case'],
    'header-max-length': [2, 'always', 100],
  },
};
