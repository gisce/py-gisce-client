# -*- coding: utf-8 -*-
from __future__ import absolute_import
import uuid
import pytest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from gisce.xmlrpc import XmlRpcClient


class TestXmlRpcRequestId(object):
    """Test that X-Request-Id header is added to XmlRpc requests"""

    def test_xmlrpc_transport_adds_request_id(self):
        """Test that XmlRpcClient transport adds X-Request-Id header"""
        # Mock the ServerProxy and its methods
        with patch('gisce.xmlrpc.ServerProxy') as mock_server_proxy:
            # Setup mocks for each ServerProxy instance
            mock_common = Mock()
            mock_common.login.return_value = 1
            
            mock_object = Mock()
            mock_object.obj_list.return_value = ['test.model']
            
            mock_report = Mock()
            
            # Configure ServerProxy to return different mocks based on URL
            def server_proxy_factory(url, **kwargs):
                if 'common' in url:
                    return mock_common
                elif 'report' in url:
                    return mock_report
                else:
                    return mock_object
            
            mock_server_proxy.side_effect = server_proxy_factory
            
            # Create client
            XmlRpcClient(
                url='http://localhost:8069',
                database='test_db',
                user='admin',
                password='admin'
            )
            
            # Verify that transport was created
            assert mock_server_proxy.call_count == 3
            
            # Check that BaseTransportWithRequestId was used (verify=None case)
            transport_arg = mock_server_proxy.call_args_list[0][1].get('transport')
            assert transport_arg is not None
            assert isinstance(transport_arg, XmlRpcClient.BaseTransportWithRequestId)

    def test_xmlrpc_unverified_transport_adds_request_id(self):
        """Test that XmlRpcClient unverified transport adds X-Request-Id header"""
        with patch('gisce.xmlrpc.ServerProxy') as mock_server_proxy:
            # Setup mocks
            mock_common = Mock()
            mock_common.login.return_value = 1
            
            mock_object = Mock()
            mock_object.obj_list.return_value = ['test.model']
            
            mock_report = Mock()
            
            def server_proxy_factory(url, **kwargs):
                if 'common' in url:
                    return mock_common
                elif 'report' in url:
                    return mock_report
                else:
                    return mock_object
            
            mock_server_proxy.side_effect = server_proxy_factory
            
            # Create client with verify=False
            client = XmlRpcClient(
                url='http://localhost:8069',
                database='test_db',
                user='admin',
                password='admin',
                verify=False
            )
            
            # Verify that UnverifiedSSLTransport was used
            transport_arg = mock_server_proxy.call_args_list[0][1].get('transport')
            assert transport_arg is not None
            assert isinstance(transport_arg, XmlRpcClient.UnverifiedSSLTransport)

    def test_transport_send_content_adds_header(self):
        """Test that transport's send_content method adds X-Request-Id"""
        # Create a transport instance
        transport = XmlRpcClient.BaseTransportWithRequestId()
        
        # Mock connection
        mock_connection = Mock()
        
        # Call send_content
        transport.send_content(mock_connection, b'<test>data</test>')
        
        # Verify putheader was called with X-Request-Id
        assert mock_connection.putheader.called
        call_args = mock_connection.putheader.call_args_list
        
        # Find the X-Request-Id header call
        x_request_id_call = None
        for call in call_args:
            if call[0][0] == 'X-Request-Id':
                x_request_id_call = call
                break
        
        assert x_request_id_call is not None, "X-Request-Id header was not added"
        
        # Verify it's a valid UUID4
        request_id = x_request_id_call[0][1]
        try:
            uuid_obj = uuid.UUID(request_id, version=4)
            assert str(uuid_obj) == request_id
        except (ValueError, AttributeError):
            pytest.fail("X-Request-Id is not a valid UUID4")

    def test_unverified_transport_send_content_adds_header(self):
        """Test that UnverifiedSSLTransport's send_content adds X-Request-Id"""
        # Create a transport instance
        transport = XmlRpcClient.UnverifiedSSLTransport()
        
        # Mock connection
        mock_connection = Mock()
        
        # Call send_content
        transport.send_content(mock_connection, b'<test>data</test>')
        
        # Verify putheader was called with X-Request-Id
        assert mock_connection.putheader.called
        call_args = mock_connection.putheader.call_args_list
        
        # Find the X-Request-Id header call
        x_request_id_call = None
        for call in call_args:
            if call[0][0] == 'X-Request-Id':
                x_request_id_call = call
                break
        
        assert x_request_id_call is not None, "X-Request-Id header was not added"
        
        # Verify it's a valid UUID4
        request_id = x_request_id_call[0][1]
        try:
            uuid_obj = uuid.UUID(request_id, version=4)
            assert str(uuid_obj) == request_id
        except (ValueError, AttributeError):
            pytest.fail("X-Request-Id is not a valid UUID4")
