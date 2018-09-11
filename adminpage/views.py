import requests
import datetime
import time
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from wechat.views import CustomWeChatView
from wechat.wrapper import WeChatView,WeChatLib
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from WeChatTicket.settings import SITE_DOMAIN
import os


from codex.baseerror import *
from codex.baseview import APIView

from wechat.models import User,Activity,Ticket
from django.shortcuts import render

STATUS_PUBLISHED = 1


# Create your views here.
############################################################################
class authLogin(APIView):
    def get(self):
        if not self.request.user.is_authenticated():
            raise ValidateError(self.input)

    def post(self):
        self.check_input('username', 'password')
        try:
            user = auth.authenticate(username=self.input['username'], password=self.input['password'])
            if not user:
                raise ValidateError("用户不存在")
            auth.login(self.request, user)
        except:
            raise ValidateError("登录失败")

class authLogout(APIView):
    def post(self):
        try:
            auth.logout(self.request)
        except:
            raise ValidateError("登出失败")


class ActivityList(APIView):
    def get(self):
        if self.request.user.is_authenticated():
            activities = []
            acts = Activity.objects.all()
            for act in acts:
                if act.status>0:
                    act_info = {}
                    act_info['id'] = act.id, ####################
                    act_info['name'] = act.name
                    act_info['description'] = act.description
                    act_info['startTime'] = act.start_time.timestamp()
                    act_info['endTime'] = act.end_time.timestamp()
                    act_info['place'] = act.place
                    act_info['bookStart'] = act.book_start.timestamp()
                    act_info['bookEnd'] = act.book_end.timestamp()
                    act_info['currentTime'] = datetime.datetime.now().timestamp()
                    act_info['status'] = act.status

                    activities.append(act_info)

            return activities
        else:
            raise ValidateError('ActivityList Error')

class ActivityDelete(APIView):
    def post(self):
            self.check_input('id')
            try:
                Activity.objects.filter(id=self.input['id']).delete()
            except:
                raise ValidateError("删除失败")

class ActivityCreate(APIView):
    def post(self):
        if self.request.user.is_authenticated():
            self.check_input('name', 'key', 'place', 'description', 'picUrl', 'startTime',
                         'endTime', 'bookStart', 'bookEnd', 'totalTickets', 'status')

            try:
                new_activity = Activity(name=self.input['name'],
                                        key=self.input['key'],
                                        place = self.input['place'],
                                        description = self.input['description'],
                                        pic_url = self.input['picUrl'],
                                        start_time = self.input['startTime'],
                                        end_time = self.input['endTime'],
                                        book_start = self.input['bookStart'],
                                        book_end=self.input['bookEnd'],
                                        total_tickets = self.input['totalTickets'],
                                        status = self.input['status'],
                                        remain_tickets=self.input['totalTickets']
                                        )
                new_activity.save()
            except:
                raise ValidateError('创建失败')
            else:
                return new_activity.id

        else:
            raise ValidateError('没有登录')

class ImageUpload(APIView):
    def post(self):
        if self.request.user.is_authenticated():
            self.check_input('image')

            try:
                ImageFile = self.input['image'][0]
                fp = open("static/img/" + ImageFile.name, 'wb')
                for i in ImageFile.chunks():
                    fp.write(i)
                fp.close()
                return SITE_DOMAIN + '/img/' + ImageFile.name
            except:
                raise ValidateError("上传失败")
        ####

class ActivityDetailA(APIView):
    def get(self):
        if self.request.user.is_authenticated():
            self.check_input('id')
            act = Activity.objects.get(id=self.input['id'])

            bookedNum = 0
            usedNum = 0

            tics = Ticket.objects.all()

            for ticket in tics:
                if(ticket.activity_id == act.id):
                    if ticket.status == Ticket.STATUS_VALID:
                        bookedNum += 1
                    elif ticket.status == Ticket.STATUS_USED:
                        usedNum += 1

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
                'bookedTickets':bookedNum,
                'usedTickets':usedNum,
                'currentTime':datetime.datetime.now().timestamp(),
                'status':act.status
            }
    def post(self):
        if self.request.user.is_authenticated():

            self.check_input('name', 'id', 'place', 'description', 'picUrl', 'startTime',
                             'endTime', 'bookStart', 'bookEnd', 'totalTickets', 'status')
            act = Activity.objects.get(id=self.input['id'])

            try:
                act.id = self.input['id']
                #if act.status == STATUS_PUBLISHED:
                act.name = self.input['name']
                act.place = self.input['place']
                act.book_start = self.input['bookStart']
                    #if self.input['status'] == STATUS_PUBLISHED:
                act.status = self.input['status']
                #if act.end_time < datetime.datetime.now().timestamp():
                act.start_time = self.input['startTime']
                act.end_time = self.input['endTime']
                #if act.start_time < datetime.datetime.now().timestamp():
                act.book_end = self.input['bookEnd']
                #if act.book_start < datetime.datetime.now().timestamp():
                act.total_tickets = self.input['totalTickets']
                act.description = self.input['description']
                act.pic_url = self.input['picUrl']
                act.save()
            except:
                raise ValidateError('修改失败')

activities = []

class ActivityMenu(APIView):
    def get(self):
        if self.request.user.is_authenticated():
            allActs = Activity.objects.all()
            activities = []
            index = 1

            current_menu = CustomWeChatView.lib.get_wechat_menu()
            existed_buttons = list()
            for btn in current_menu:
                if btn['name'] == '抢票':
                    existed_buttons += btn.get('sub_button', list())
            activity_ids = list()
            for btn in existed_buttons:
                if 'key' in btn:
                    activity_id = btn['key']
                    if activity_id.startswith(CustomWeChatView.event_keys['book_header']):
                        activity_id = activity_id[len(CustomWeChatView.event_keys['book_header']):]
                    if activity_id and activity_id.isdigit():
                        activity_ids.append(int(activity_id))
            acts = Activity.objects.filter(
                id__in=activity_ids, status=Activity.STATUS_PUBLISHED, book_end__gt=timezone.now()
            ).order_by('book_end')[: 5]

            for act in acts:
                act_info = {}
                act_info['id'] = act.id
                act_info['name'] = act.name
                act_info['menuIndex'] = index
                index += 1
                activities.append(act_info)

            for act in allActs:
                if act not in acts:
                    if act.book_end.timestamp() > datetime.datetime.now().timestamp() and act.status == STATUS_PUBLISHED:
                        act_info = {}
                        act_info['id'] = act.id
                        act_info['name'] = act.name
                        act_info['menuIndex'] = 0
                        activities.append(act_info)

            return activities

    def post(self):
        if self.request.user.is_authenticated():
            activities = [Activity.objects.get(id=id) for id in self.input]
            CustomWeChatView.update_menu(activities)
            #####

class ActivityCheckin(APIView):
    def post(self):
        if self.request.user.is_authenticated():
            try:
                try:
                    self.input['ticket']
                except:
                    self.check_input('actId', 'studentId')
                    if Ticket.objects.filter(activity_id=self.input['actId'], student_id=self.input['studentId']):
                        tic = Ticket.objects.get(activity_id=self.input['actId'], student_id=self.input['studentId'])
                        if not tic.status == Ticket.STATUS_CANCELLED:
                            return {
                                'ticket': tic.unique_id,
                                'studentId': tic.student_id
                            }

                try:
                    self.input['studentId']
                except:
                    self.check_input('actId', 'ticket')
                    if Ticket.objects.filter(activity_id=self.input['actId'], unique_id=self.input['ticket']):
                        tic = Ticket.objects.get(activity_id=self.input['actId'], unique_id=self.input['ticket'])
                        if not tic.status == Ticket.STATUS_CANCELLED:
                            return {
                                'ticket': tic.unique_id,
                                'studentId': tic.student_id
                            }

                raise ValidateError("没有响应的电子票")

            except:
                raise ValidateError("没有响应的电子票")


            #####

##############################################################