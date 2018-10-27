from django.contrib import admin
from df_goods.models import *
from django.core.cache import cache


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        print('新增修改')
        '''新增或者更新表中的数据时调用'''
        super().save_model(request, obj, form, change)

        #发出任务，让celery worker重新生成首页静态页
        from celery_task.tasks import task_generate_static_index

        task_generate_static_index.delay()
        cache.delete('cache_index')

    def delete_model(self, request, obj):
        '''删除表中的数据时调用'''
        super().save_model(request, request,obj)

        # 发出任务，让celery worker重新生成首页静态页
        from celery_task.tasks import task_generate_static_index
        task_generate_static_index.delay()
        cache.delete('cache_index')

class GoodsTypeAdmin(BaseAdmin):
    pass

class GoodsSKUAdmin(BaseAdmin):
    pass

class GoodsAdmin(BaseAdmin):
    pass

class IndexGoodsBannerAdmin(BaseAdmin):
    pass

class IndexTypeGoodsBannerAdmin(BaseAdmin):
    pass

class IndexPromotionBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(Goods,GoodsAdmin)
admin.site.register(GoodImage)
admin.site.register(IndexGoodsBanner,IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner,IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)