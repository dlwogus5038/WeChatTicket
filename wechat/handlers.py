# -*- coding: utf-8 -*-
#
from wechat.wrapper import WeChatHandler
from wechat.models import Activity,Ticket
from WeChatTicket.settings import get_url
from django.core.exceptions import ObjectDoesNotExist
import datetime
import uuid


__author__ = "Epsirom"


class ErrorHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，服务器现在有点忙，暂时不能给您答复 T T')


class DefaultHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，没有找到您需要的信息:(')


class HelpOrSubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('帮助', 'help') or self.is_event('scan', 'subscribe') or \
               self.is_event_click(self.view.event_keys['help'])

    def handle(self):
        return self.reply_single_news({
            'Title': self.get_message('help_title'),
            'Description': self.get_message('help_description'),
            'Url': self.url_help(),
        })


class UnbindOrUnsubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('解绑') or self.is_event('unsubscribe')

    def handle(self):
        self.user.student_id = ''
        self.user.save()
        return self.reply_text(self.get_message('unbind_account'))


class BindAccountHandler(WeChatHandler):

    def check(self):
        return self.is_text('绑定') or self.is_event_click(self.view.event_keys['account_bind'])

    def handle(self):
        return self.reply_text(self.get_message('bind_account'))


class BookEmptyHandler(WeChatHandler):

    def check(self):
        return self.is_event_click(self.view.event_keys['book_empty'])

    def handle(self):
        return self.reply_text(self.get_message('book_empty'))

###########################################################################
class BookWhatHandler(WeChatHandler):

    def check(self):
        return self.is_text('抢啥') or self.is_event_click(self.view.event_keys['book_what'])

    def handle(self):
        activities = []
        acts = Activity.objects.all()
        for act in acts:
            if act.book_end.timestamp() > datetime.datetime.now().timestamp():
                act_info = {
                    'Title': act.name,
                    'Description': act.description,
                    'PicUrl': act.pic_url,
                    'Url': get_url('u/activity', {'id': act.id}),
                }
                activities.append(act_info)

        return self.reply_news(activities)


class BookHeaderHandler(WeChatHandler):
    def check(self):
        acts = Activity.objects.all()

        for act in acts:
            if self.is_text('抢票 ' + act.key) or self.is_event_click(self.view.event_keys['book_header'] + str(act.id)):
                return True

        return False

    def handle(self):
        if not self.user.student_id:
            return self.reply_text('需要绑定学号')

        acts = Activity.objects.all()
        for act in acts:
            if self.is_text('抢票 ' + act.key) or self.is_event_click(self.view.event_keys['book_header'] + str(act.id)):
                break

        if not Ticket.objects.filter(activity_id=act.id,student_id=self.user.student_id):
            if act.remain_tickets <= 0:
                return self.reply_text('没有剩余的票')
            if act.book_start.timestamp() > datetime.datetime.now().timestamp():
                return self.reply_text('还没到抢票开始时间')
            tic = Ticket()
            tic.student_id = self.user.student_id
            tic.unique_id = uuid.uuid1()
            tic.activity_id = act.id
            tic.status = Ticket.STATUS_VALID
            tic.save()

            act.remain_tickets -= 1
            act.save()

            return self.reply_single_news({
                'Title': '抢票成功！！',
                'PicUrl': act.pic_url,
                'Description': '活动名称 : ' + str(act.name) +
                                '\nstudent_id = ' + str(tic.student_id) +
                                '\nunique_id = ' + str(tic.unique_id) +
                                '\nactivity_name = ' + str(Activity.objects.get(id=act.id).name) +
                                '\nstatus = ' + str(tic.status) +
                                '\nremain_tickets = ' + str(Activity.objects.get(id=act.id).remain_tickets),
                'Url': get_url('u/ticket', {'openid': self.user.open_id, 'ticket': tic.unique_id}),
                })
        elif Ticket.objects.get(activity_id=act.id,student_id=self.user.student_id).status == Ticket.STATUS_CANCELLED:
            tic = Ticket.objects.get(activity_id=act.id,student_id=self.user.student_id)
            tic.status = Ticket.STATUS_VALID
            tic.save()

            act.remain_tickets -= 1
            act.save()
            
            return self.reply_single_news({
                'Title': '抢票成功！！',
                'PicUrl': act.pic_url,
                'Description': '活动名称 : ' + str(act.name) +
                               '\nstudent_id = ' + str(tic.student_id) +
                               '\nunique_id = ' + str(tic.unique_id) +
                               '\nactivity_name = ' + str(Activity.objects.get(id=act.id).name) +
                               '\nstatus = ' + str(tic.status) +
                               '\nremain_tickets = ' + str(Activity.objects.get(id=act.id).remain_tickets),
                'Url': get_url('u/ticket', {'openid': self.user.open_id, 'ticket': tic.unique_id}),
            })
        else:
            tic = Ticket.objects.get(activity_id=act.id, student_id=self.user.student_id)
            return self.reply_single_news({
                'Title': '已经抢过！',
                'PicUrl': act.pic_url,
                'Description': '点击(详细)就能看到电子票信息',
                'Url': get_url('u/ticket', {'openid': self.user.open_id, 'ticket': tic.unique_id}),
            })

            #return self.reply_text('抢票成功,\nstudent_id = ' + str(tic.student_id) +
             #                              '\nunique_id = ' + str(tic.unique_id) +
              #                             '\nactivity_name = ' + str(Activity.objects.get(id=act.id).name) +
               #                            '\nstatus = ' + str(tic.status) +
                #                           '\nremain_tickets = ' + str(Activity.objects.get(id=act.id).remain_tickets)
                 #                          )

class GetTicketHandler(WeChatHandler):
    def check(self):
        if  self.is_text('查票') or self.is_event_click(self.view.event_keys['get_ticket']):
            return True

    def handle(self):
        if not self.user.student_id:
            return self.reply_text('需要绑定学号')

        if not Ticket.objects.filter(student_id=self.user.student_id):
            return self.reply_text('没有抢到的票')

        tickets = []

        tics = Ticket.objects.all()
        for tic in tics:
            if tic.status == Ticket.STATUS_VALID and tic.student_id == self.user.student_id:
                tic_info = {
                    'Title': '电子票的活动名称 : ' + str(Activity.objects.get(id=tic.activity_id).name),
                    'Url': get_url('u/ticket', {'openid': self.user.open_id, 'ticket': tic.unique_id}),
                }
                tickets.append(tic_info)

        return self.reply_news(tickets)

class CancelTicketHandler(WeChatHandler):
    def check(self):
        acts = Activity.objects.all()

        for act in acts:
            if self.is_text('退票 ' + act.key):
                return True

        return False

    def handle(self):
        if not self.user.student_id:
            return self.reply_text('需要绑定学号')

        acts = Activity.objects.all()

        for act in acts:
            if self.is_text('退票 ' + act.key):
                break

        if not Ticket.objects.filter(activity_id=act.id,student_id=self.user.student_id):
            return self.reply_text('没有抢到这个活动的票')
        elif Ticket.objects.get(activity_id=act.id,student_id=self.user.student_id).status == Ticket.STATUS_CANCELLED:
            return self.reply_text('已经退过')
        else:
            act.remain_tickets += 1
            act.save()

            tic = Ticket.objects.get(activity_id=act.id,student_id=self.user.student_id)
            tic.status = Ticket.STATUS_CANCELLED
            tic.save()
            return self.reply_text('退票成功！！'
                                   '\nremain_tickets : ' + str(act.remain_tickets))

###########################################################################

class CalculateHandler(WeChatHandler):

    def check(self):
        return self.is_calculate()

    def handle(self):
        try:
            value = eval(self.input['Content'])
        except:
            return self.reply_text("输入的表达式是非法的")
        else:
            return self.reply_text(str(eval(self.input['Content'])))