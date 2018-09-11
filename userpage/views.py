import requests
import datetime
import time
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from codex.baseerror import *
from codex.baseview import APIView

from wechat.models import User,Activity,Ticket

STATUS_PUBLISHED = 1

class UserBind(APIView):

    def validate_user(self):
        #'''
        url = 'https://id.tsinghua.edu.cn/security_check'

        user_info = {'username':self.input['student_id'],'password':self.input['password']}

        re_post = requests.post(url=url,data=user_info,verify=True)

        if 'setting' not in re_post.url:
            raise ValidateError(self.input)
            #'''
        """
        input: self.input['student_id'] and self.input['password']
        raise: ValidateError when validating failed
        """
        # raise NotImplementedError('You should implement UserBind.validate_user method')

    def get(self):
        self.check_input('openid')
        return User.get_by_openid(self.input['openid']).student_id

    def post(self):
        self.check_input('openid', 'student_id', 'password')
        user = User.get_by_openid(self.input['openid'])
        self.validate_user()
        user.student_id = self.input['student_id']
        user.save()

###########################################################################
class ActivityDetail(APIView):
    def get(self):
        self.check_input('id')
        act = Activity.objects.get(id=self.input['id'])
        if act.status == STATUS_PUBLISHED:
            return {
                'name':act.name,
                'key':act.key,
                'description':act.description,
                'startTime':act.start_time.timestamp(),
                'endTime':act.end_time.timestamp(),
                'place':act.place,
                'bookStart':act.book_start.timestamp(),
                'bookEnd':act.book_end.timestamp(),
                'totalTickets':act.total_tickets,
                'picUrl':act.pic_url,
                'remainTickets':act.remain_tickets,
                'currentTime':datetime.datetime.now().timestamp()
            }
        else:
            raise ValidateError('ActivityDetail Error')

class TicketDetail(APIView):
    def get(self):
        self.check_input('openid','ticket')
        user = User.get_by_openid(self.input['openid'])
        ticket = Ticket.objects.get(unique_id=self.input['ticket'])
        act = Activity.objects.get(id=ticket.activity_id)
        return {
            'activityName':act.name,
            'place':act.place,
            'activityKey':act.key,
            'uniqueId':ticket.unique_id,
            'startTime':act.start_time.timestamp(),
            'endTime':act.end_time.timestamp(),
            'currentTime':datetime.datetime.now().timestamp(),
            'status':ticket.status
        }
###########################################################################