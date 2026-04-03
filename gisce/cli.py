# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import argparse
import json
import sys
from . import connect


def build_parser():
    parser = argparse.ArgumentParser(
        prog='pygisceclient',
        description='Command-line client for the GISCE ERP',
    )
    parser.add_argument(
        '--url',
        required=True,
        help=(
            'Connection URL including the protocol prefix, e.g. '
            'https+xmlrpc://erp.example.com'
        ),
    )
    parser.add_argument(
        '--database', '-d',
        required=True,
        help='Database name',
    )

    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument(
        '--token',
        help='Authentication token',
    )
    auth.add_argument(
        '--user', '-u',
        help='Username for authentication',
    )

    parser.add_argument(
        '--password', '-p',
        help='Password for authentication (required when --user is used)',
    )
    parser.add_argument(
        '--model', '-m',
        required=True,
        help='Model name, e.g. res.users',
    )
    parser.add_argument(
        '--method',
        required=True,
        help='Method name to call on the model, e.g. search',
    )
    parser.add_argument(
        '--args',
        default='[]',
        help='Positional arguments as a JSON array (default: [])',
    )
    parser.add_argument(
        '--kwargs',
        default='{}',
        help='Keyword arguments as a JSON object (default: {})',
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        dest='no_verify',
        help='Disable SSL certificate verification',
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.user and not args.password:
        parser.error('--password is required when --user is provided')

    try:
        call_args = json.loads(args.args)
    except ValueError as exc:
        parser.error('Invalid JSON for --args: {}'.format(exc))

    try:
        call_kwargs = json.loads(args.kwargs)
    except ValueError as exc:
        parser.error('Invalid JSON for --kwargs: {}'.format(exc))

    if not isinstance(call_args, list):
        parser.error('--args must be a JSON array')

    if not isinstance(call_kwargs, dict):
        parser.error('--kwargs must be a JSON object')

    connect_kwargs = {
        'verify': not args.no_verify,
    }
    if args.token:
        connect_kwargs['token'] = args.token
    else:
        connect_kwargs['user'] = args.user
        connect_kwargs['password'] = args.password

    try:
        client = connect(args.url, args.database, **connect_kwargs)
    except Exception as exc:
        print('Error connecting to {}: {}'.format(args.url, exc), file=sys.stderr)
        sys.exit(1)

    if client is None:
        print(
            'Unsupported protocol in URL: {}. '
            'Use a prefix like https+xmlrpc://, https+restapi://, etc.'.format(args.url),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        model = client.model(args.model)
        method = getattr(model, args.method)
        result = method(*call_args, **call_kwargs)
    except Exception as exc:
        print('Error calling {}.{}: {}'.format(args.model, args.method, exc), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
