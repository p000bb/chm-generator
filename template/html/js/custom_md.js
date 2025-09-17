// 给技术资源点击的a标签添加name参数
function addNameToHref() {
    // 动态获取当前页面名称
    function getCurrentPageName() {
        // 从.headertitle > .title的innerText获取
        const $headerTitle = $('.headertitle > .title');
        if ($headerTitle.length) {
            return $headerTitle.text().trim();
        }
        return null;
    }

    const currentPageName = getCurrentPageName();

    if (!currentPageName) return;

    // 为所有技术资源链接添加点击事件，点击时在URL hash中设置芯片名称
    const $resourceLinks = $('.href-list .el');

    $resourceLinks.each(function () {
        const $link = $(this);

        // 添加点击事件
        $link.on('click', function () {
            // 点击时在URL hash中设置芯片名称
            const currentUrl = $link.attr('href');
            if (currentUrl) {
                const separator = currentUrl.indexOf('#') !== -1 ? '&' : '#';
                const newUrl = currentUrl + separator + 'chip=' + currentPageName;
                $link.attr('href', newUrl);
                console.log('设置链接hash:', newUrl);
            }
        });
    });
}

// 隐藏标签内容包含芯片名称的标签
function hideChipName() {
    // 从URL hash中获取芯片名称
    function getChipNameFromHash() {
        const hash = window.location.hash;
        if (hash) {
            // 查找chip=参数
            const match = hash.match(/chip=([^&#]*)/);
            if (match) {
                return decodeURIComponent(match[1]);
            }
        }
        return '';
    }

    const chipName = getChipNameFromHash();

    if (!chipName) return;

    // 查找contents区域
    const $contents = $('div.contents');
    if (!$contents.length) {
        return;
    }

    // 判断当前语言并显示对应的返回文本
    function getBackText() {
        const currentUrl = window.location.href;
        if (currentUrl.indexOf('/cn/') !== -1) {
            return '← 返回上一级';
        } else if (currentUrl.indexOf('/en/') !== -1) {
            return '← Back';
        } else {
            // 默认中文
            return '← 返回上一级';
        }
    }

    // 在.contents下面添加返回上一级的链接
    const $backLink = $('<div>').css('margin-bottom', '20px')
        .html('<a href="javascript:history.back()">' + getBackText() + '</a>');

    // 将返回链接插入到contents的最前面
    $contents.prepend($backLink);
    $backLink.show();

    // 查找所有.file-link元素
    const $fileLinks = $('.file-link');

    $fileLinks.each(function () {
        const $fileLink = $(this);
        const linkText = $fileLink.text();

        // 检查当前file-link的文本是否包含芯片名称
        if (linkText.indexOf(chipName) === -1) {
            // 不包含芯片名称，向上查找tr节点并隐藏
            const $tr = $fileLink.closest('tr');
            if ($tr.length) {
                $tr.css('display', 'none');
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    addNameToHref();
    hideChipName();
});