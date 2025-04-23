WORLDANVIL_SECRET_SCHEMA={
    'WorldAnvil': {
        'required': False,
        'type': 'dict',
        'allowed': ['credentials', 'track', 'remote_repo'],
        'schema': {
            'credentials': {
                'required': True,
                'type': 'dict',
                'nullable': False,
                'schema': {
                    'application_key': {
                        'required': True,
                        'type': 'string',
                        'nullable': False,
                        'regex': '[a-f0-9]{128}'
                    },
                    'authentication_token': {
                        'required': True,
                        'type': 'string',
                        'nullable': False,
                        'regex': '[a-zA-Z0-9]{249}'
                    }
                }
            },
            'track': {
                'required': True,
                'type': 'dict',
                'nullable': False,
                'schema': {
                    'worlds': {
                        'required': True,
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'url': {
                                    'required': True,
                                    'type': 'string',
                                    'nullable': False,
                                    'regex': r'https://[a-zA-Z0-9\.\-\/]{1,50}'
                                },
                                'track_changes': {
                                    'required': True,
                                    'type': 'dict',
                                    'nullable': True,
                                    'allowed': ['categories', 'articles', 'article_blocks', 'images', 'maps'],
                                    'schema': {
                                        'categories': {
                                            'required': False,
                                            'type': 'boolean',
                                            'nullable': False
                                        },
                                        'articles': { 
                                            'required': False,
                                            'type': 'boolean',
                                            'nullable': False
                                        },
                                        'article_blocks': { 
                                            'required': False,
                                            'type': 'boolean',
                                            'nullable': False
                                        },
                                        'images': { 
                                            'required': False,
                                            'type': 'boolean',
                                            'nullable': False
                                        },
                                        'maps': { 
                                            'required': False,
                                            'type': 'boolean',
                                            'nullable': False
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'remote_repo': {
                'required': True,
                'type': 'dict',
                'allowed': ['remote_repository_url'],
                'schema': {
                    'remote_repository_url': {
                        'required': True,
                        'type': 'string',
                        'nullable': False,
                        'regex': r'git@github.com:[a-zA-Z0-9]{1,15}/[a-zA-Z0-9\-]{1,35}.git'
                    }
                }
            }
        }
    }
}

