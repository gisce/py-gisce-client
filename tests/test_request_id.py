# -*- coding: utf-8 -*-
from __future__ import absolute_import
import uuid
import pytest
import responses
from gisce.restapi import RestApiClient
from gisce.msgpack import MsgPackClient


class TestRequestIdHeader(object):
    """Test that X-Request-Id header is added to all requests"""

    @responses.activate
    def test_restapi_client_adds_request_id(self):
        """Test RestApiClient adds X-Request-Id header"""
        # Mock fields_get call
        responses.add(
            responses.POST,
            'http://localhost:5000/RestApiModel/fields_get',
            json={'res': {}},
            status=200
        )
        
        # Mock the API endpoint
        responses.add(
            responses.POST,
            'http://localhost:5000/RestApiModel/test_method',
            json={'res': 'success'},
            status=200
        )
        
        # Create client and make a request
        client = RestApiClient(
            url='http://localhost:5000',
            user='test',
            password='test'
        )
        model = client.model('rest.api.model')
        model.test_method()
        
        # Verify X-Request-Id header was sent
        assert len(responses.calls) == 2
        # Check the actual test_method call (second request)
        request_headers = responses.calls[1].request.headers
        assert 'X-Request-Id' in request_headers
        # Verify it's a valid UUID4
        request_id = request_headers['X-Request-Id']
        try:
            uuid_obj = uuid.UUID(request_id, version=4)
            assert str(uuid_obj) == request_id
        except (ValueError, AttributeError):
            pytest.fail("X-Request-Id is not a valid UUID4")

    @responses.activate
    def test_msgpack_client_adds_request_id_json(self):
        """Test MsgPackClient adds X-Request-Id header with JSON content type"""
        # Mock the login endpoint
        responses.add(
            responses.POST,
            'http://localhost:5000/common',
            json=123,  # uid
            status=200
        )
        
        # Mock the obj_list endpoint
        responses.add(
            responses.POST,
            'http://localhost:5000/object',
            json=['model1', 'model2'],
            status=200
        )
        
        # Create client
        MsgPackClient(
            url='http://localhost:5000',
            database='test_db',
            user='test',
            password='test',
            content_type='json'
        )
        
        # Verify X-Request-Id header was sent in all requests
        assert len(responses.calls) == 2
        for call in responses.calls:
            request_headers = call.request.headers
            assert 'X-Request-Id' in request_headers
            # Verify it's a valid UUID4
            request_id = request_headers['X-Request-Id']
            try:
                uuid_obj = uuid.UUID(request_id, version=4)
                assert str(uuid_obj) == request_id
            except (ValueError, AttributeError):
                pytest.fail("X-Request-Id is not a valid UUID4")

    @responses.activate
    def test_msgpack_client_model_call_adds_request_id(self):
        """Test MsgPackClient model calls add X-Request-Id header"""
        # Mock the login endpoint
        responses.add(
            responses.POST,
            'http://localhost:5000/common',
            json=123,  # uid
            status=200
        )
        
        # Mock the obj_list endpoint
        responses.add(
            responses.POST,
            'http://localhost:5000/object',
            json=['test.model'],
            status=200
        )
        
        # Mock fields_get call
        responses.add(
            responses.POST,
            'http://localhost:5000/object',
            json={},
            status=200
        )
        
        # Mock a model method call
        responses.add(
            responses.POST,
            'http://localhost:5000/object',
            json={'success': True},
            status=200
        )
        
        # Create client and make a model call
        client = MsgPackClient(
            url='http://localhost:5000',
            database='test_db',
            user='test',
            password='test',
            content_type='json'
        )
        model = client.model('test.model')
        model.search([])
        
        # Verify X-Request-Id header was sent in all requests (login, obj_list, fields_get, search)
        assert len(responses.calls) == 4
        for call in responses.calls:
            request_headers = call.request.headers
            assert 'X-Request-Id' in request_headers

    @responses.activate
    def test_each_request_gets_unique_request_id(self):
        """Test that each request gets a different X-Request-Id"""
        # Mock fields_get call
        responses.add(
            responses.POST,
            'http://localhost:5000/TestModel/fields_get',
            json={'res': {}},
            status=200
        )
        
        # Mock multiple endpoints
        for _ in range(3):
            responses.add(
                responses.POST,
                'http://localhost:5000/TestModel/test_method',
                json={'res': 'success'},
                status=200
            )
        
        # Create client
        client = RestApiClient(
            url='http://localhost:5000',
            user='test',
            password='test'
        )
        model = client.model('test.model')
        
        # Make multiple requests
        model.test_method()
        model.test_method()
        model.test_method()
        
        # Collect all request IDs (skip first call which is fields_get)
        request_ids = []
        for call in responses.calls[1:]:  # Skip fields_get call
            request_id = call.request.headers['X-Request-Id']
            request_ids.append(request_id)
        
        # Verify all request IDs are unique
        assert len(request_ids) == 3
        assert len(set(request_ids)) == 3, "Request IDs should be unique"
