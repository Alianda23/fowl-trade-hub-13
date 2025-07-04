
from flask import Blueprint, request, jsonify
import requests
import base64
from datetime import datetime
import json
import socket

mpesa_routes = Blueprint('mpesa', __name__)

# M-Pesa API credentials
CONSUMER_KEY = "eUb7fiTHhwdNdiAcNgAoJlziG7sZRfnyBu6eBENXS2OqyLGh"
CONSUMER_SECRET = "LSk070XeJmvHg1OIg39Bl3QgeBCEMM3XMgrKVZDGt5S96wFsTnVJqn2kGyRAO10h"
BUSINESS_SHORT_CODE = "174379"  # Lipa Na M-Pesa shortcode
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Lipa Na M-Pesa passkey
CALLBACK_URL = "http://localhost:5000/api/mpesa/callback"  # Local development callback URL

# M-Pesa API endpoints
API_BASE_URL = "https://sandbox.safaricom.co.ke"
AUTH_ENDPOINT = "/oauth/v1/generate"
STK_PUSH_ENDPOINT = "/mpesa/stkpush/v1/processrequest"

# Store transaction details in memory (in a real app, you'd use a database)
TRANSACTIONS = {}

@mpesa_routes.route('/stkpush', methods=['POST'])
def initiate_stk_push():
    try:
        data = request.json
        phone_number = data.get('phoneNumber')
        amount = data.get('amount', 1)  # Default to 1 if not provided
        
        if not phone_number:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
        
        # Check internet connectivity first
        if not check_internet_connection():
            return jsonify({
                'success': False,
                'message': 'No internet connection. Please check your network and try again.'
            }), 503
        
        # Check if M-Pesa API is reachable
        if not is_mpesa_api_reachable():
            return jsonify({
                'success': False,
                'message': 'Unable to reach M-Pesa API. Please try again later.'
            }), 503
        
        # Get access token
        access_token_result = get_access_token()
        if 'error' in access_token_result:
            return jsonify({
                'success': False,
                'message': 'Failed to authenticate with M-Pesa',
                'details': access_token_result['error']
            }), 500
        
        access_token = access_token_result['access_token']
        
        # Prepare timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate password - format: BusinessShortCode+Passkey+Timestamp
        password = base64.b64encode(f"{BUSINESS_SHORT_CODE}{PASSKEY}{timestamp}".encode()).decode('utf-8')
        
        # Prepare STK push request
        stk_request = {
            "BusinessShortCode": BUSINESS_SHORT_CODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": BUSINESS_SHORT_CODE,
            "PhoneNumber": phone_number,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": "KukuHub",
            "TransactionDesc": "Payment for products"
        }
        
        # Make request to M-Pesa API
        try:
            response = requests.post(
                f"{API_BASE_URL}{STK_PUSH_ENDPOINT}",
                json=stk_request,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30  # Add timeout to prevent indefinite waiting
            )
            
            if response.status_code != 200:
                return jsonify({
                    'success': False,
                    'message': f'M-Pesa API returned status code {response.status_code}',
                    'details': response.text
                }), 400
                
            mpesa_response = response.json()
            
            if 'ResponseCode' in mpesa_response and mpesa_response['ResponseCode'] == '0':
                # Success - store transaction
                checkout_request_id = mpesa_response['CheckoutRequestID']
                TRANSACTIONS[checkout_request_id] = {
                    'amount': amount,
                    'phone_number': phone_number,
                    'status': 'pending',
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify({
                    'success': True,
                    'message': 'STK push sent successfully',
                    'checkoutRequestID': checkout_request_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to initiate STK push',
                    'details': mpesa_response
                }), 400
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': 'Error sending STK push request',
                'details': str(e)
            }), 500
            
    except Exception as e:
        print(f"STK push error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@mpesa_routes.route('/status/<checkout_request_id>', methods=['GET'])
def check_payment_status(checkout_request_id):
    # In a real implementation, you would check from database or make API call
    # Here we're just returning the stored transaction status
    transaction = TRANSACTIONS.get(checkout_request_id)
    
    if not transaction:
        return jsonify({
            'success': False,
            'status': 'failed',
            'message': 'Transaction not found'
        }), 404
    
    return jsonify({
        'success': True,
        'status': transaction['status'],
        'message': f"Payment {transaction['status']}",
        'details': transaction
    })

@mpesa_routes.route('/callback', methods=['POST'])
def mpesa_callback():
    """Callback endpoint for M-Pesa to send payment results"""
    try:
        data = request.json
        
        # Process callback data
        body = data.get('Body', {})
        stkCallback = body.get('stkCallback', {})
        checkout_request_id = stkCallback.get('CheckoutRequestID')
        
        if checkout_request_id in TRANSACTIONS:
            result_code = stkCallback.get('ResultCode')
            
            if result_code == 0:
                # Payment successful
                TRANSACTIONS[checkout_request_id]['status'] = 'completed'
            else:
                # Payment failed
                TRANSACTIONS[checkout_request_id]['status'] = 'failed'
                TRANSACTIONS[checkout_request_id]['result_code'] = result_code
                TRANSACTIONS[checkout_request_id]['result_desc'] = stkCallback.get('ResultDesc')
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
    except Exception as e:
        print(f"Callback processing error: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Rejected'}), 500

def get_access_token():
    """Get M-Pesa API access token"""
    try:
        credentials = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode('utf-8')
        
        response = requests.get(
            f"{API_BASE_URL}{AUTH_ENDPOINT}?grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {credentials}"
            },
            timeout=30  # Add timeout to prevent indefinite waiting
        )
        
        if response.status_code != 200:
            return {
                'error': f"API returned status code {response.status_code}: {response.text}"
            }
            
        data = response.json()
        if 'access_token' not in data:
            return {
                'error': f"No access token in response: {data}"
            }
            
        return {'access_token': data.get('access_token')}
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {str(e)}")
        return {'error': f"Connection error: {str(e)}"}
    except requests.exceptions.Timeout as e:
        print(f"Request timed out: {str(e)}")
        return {'error': f"Request timed out: {str(e)}"}
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {str(e)}")
        return {'error': f"Request error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f"Unexpected error: {str(e)}"}

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def is_mpesa_api_reachable():
    """Check if M-Pesa API is reachable"""
    try:
        # Try to connect to the M-Pesa API host
        socket.gethostbyname("sandbox.safaricom.co.ke")
        return True
    except socket.gaierror:
        return False
