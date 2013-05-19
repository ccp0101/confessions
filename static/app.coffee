$ -> 
  # adapted from https://raw.github.com/timrwood/moment/2.0.0/lang/zh-cn.js
  moment.lang "zh-cn", 
    months : "一月_二月_三月_四月_五月_六月_七月_八月_九月_十月_十一月_十二月".split("_")
    monthsShort : "1月_2月_3月_4月_5月_6月_7月_8月_9月_10月_11月_12月".split("_")
    weekdays : "星期日_星期一_星期二_星期三_星期四_星期五_星期六".split("_")
    weekdaysShort : "周日_周一_周二_周三_周四_周五_周六".split("_")
    weekdaysMin : "日_一_二_三_四_五_六".split("_")
    longDateFormat :
        LT : "Ah点mm分"
        L : "YYYY年MMMD日"
        LL : "YYYY年MMMD日"
        LLL : "YYYY年MMMD日LT"
        LLLL : "YYYY年MMMD日ddddLT"
        l : "YYYY年MMMD日"
        ll : "YYYY年MMMD日"
        lll : "YYYY年MMMD日LT"
        llll : "YYYY年MMMD日ddddLT"
    meridiem : (hour, minute, isLower) ->
        if (hour < 9)
            "早上"
        else if (hour < 11 && minute < 30)
            "上午"
        else if (hour < 13 && minute < 30)
            "中午"
        else if (hour < 18)
            "下午"
        else
            "晚上"
    calendar :
        sameDay : '[今天]LT'
        nextDay : '[明天]LT'
        nextWeek : '[下]ddddLT'
        lastDay : '[昨天]LT'
        lastWeek : '[上]ddddLT'
        sameElse : 'L'
    ordinal : (number, period) ->
        switch period
          when "d", "D", "DDD" then number + "日"
          when "M" then number + "月"
          when "w", "W" then number + "周"
          else number
    relativeTime :
        future : "%s内"
        past : "%s前"
        s : "几秒"
        m : "1分钟"
        mm : "%d分钟"
        h : "1小时"
        hh : "%d小时"
        d : "1天"
        dd : "%d天"
        M : "1个月"
        MM : "%d个月"
        y : "1年"
        yy : "%d年"

  _.each $(".datetime"), (el) ->
    $(el).text moment($(el).data("source")).format("LLL")

  $(".btn-show-publish").click (e) ->
    id = $(e.currentTarget).parents("tr").data("id")
    message = $(".message", $(e.currentTarget).parents("tr")).text()
    $(".modal-publish .message").val(message)
    $(".modal-publish").data("id", id).modal()

  $(".btn-publish").click (e) ->
    message = $(".modal-publish .message").val()
    id = $(".modal-publish").data("id")
    $.ajax
      method: "POST", 
      url: "/publish"
      data:
        message: message, id: id
      beforeSend: ->
        $.blockUI css:
          border: 'none'
          padding: '15px'
          backgroundColor: '#000'
          'border-radius': '10px'
          '-webkit-border-radius': '10px'
          '-moz-border-radius': '10px'
          opacity: .5
          "z-index": 100000
          color: '#fff'
      success: ->
        alert "发布成功！"
      error: ->
        alert "发布失败！"
      complete: ->
        document.location.reload()

  $(".btn-undo-publish").click (e) ->
    id = $(e.currentTarget).parents("tr").data("id")
    $.ajax
      method: "POST", 
      url: "/undo"
      data:
        id: id
      beforeSend: ->
        $.blockUI css:
          border: 'none'
          padding: '15px'
          backgroundColor: '#000'
          'border-radius': '10px'
          '-webkit-border-radius': '10px'
          '-moz-border-radius': '10px'
          "z-index": 100000
          opacity: .5
          color: '#fff'
      success: ->
        alert "撤销成功！"
      error: ->
        alert "撤销失败！"
      complete: ->
        document.location.reload()

  $(".btn-publish-new").click (e) ->
    message = $(".modal-publish .message").val()
    id = $(".modal-publish").data("id")
    $.ajax
      method: "POST", 
      url: "/publish"
      data:
        message: message, id: id
      beforeSend: ->
        $.blockUI css:
          border: 'none'
          padding: '15px'
          backgroundColor: '#000'
          'border-radius': '10px'
          '-webkit-border-radius': '10px'
          '-moz-border-radius': '10px'
          opacity: .5
          "z-index": 100000
          color: '#fff'
      success: ->
        alert "发布成功！"
      error: ->
        alert "发布失败！"
      complete: ->
        document.location.reload()
    